#!/usr/bin/env python3
"""TaskToAgent - heartbeat watchdog (dead man's switch). Python 3.9+, standard library only.
Alerts you when something that should run on a schedule silently STOPS running: a cron job,
a backup, an n8n workflow, a scraper. Error alerts can't catch this, because nothing errors.

  check : (default) checks every heartbeat in CHECKS_FILE and alerts Discord and/or email once when
          one goes stale, and once when it recovers.
  serve : tiny ping receiver. Your jobs call http://HOST:8765/ping/<name> when they finish
          (curl, PowerShell, an n8n HTTP Request node), and `check` treats it as a heartbeat.

Heartbeat types in checks.json (see checks.example.json):
  file : a file your job touches when it succeeds (`... && touch /var/run/backup.ok`); stale if older than max_age
  ping : a name pinged through `serve`; stale if not pinged within max_age
  n8n  : an n8n workflow id; stale if its last SUCCESSFUL execution is older than max_age (needs N8N_URL + N8N_API_KEY)
  url  : a URL that must answer HTTP 2xx (plain uptime check, no max_age)
max_age: 90s, 15m, 2h, 26h, 7d.
Usage: python3 heartbeat_watchdog.py [check|serve] [--dry-run]"""
import os, sys, re, json, ssl, time, smtplib, urllib.request, urllib.parse, urllib.error
from email.message import EmailMessage
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS_FILE = (os.getenv("CHECKS_FILE") or os.path.join(HERE, "checks.json"))
STATE = (os.getenv("STATE_FILE") or os.path.join(HERE, "watchdog_state.json"))
PINGS = (os.getenv("PINGS_FILE") or os.path.join(HERE, "pings.json"))
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
N8N = (os.getenv("N8N_URL") or "http://localhost:5678").rstrip("/")
KEY = os.getenv("N8N_API_KEY", "")
DRY = "--dry-run" in sys.argv
UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

def secs(v):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhd]?)\s*", str(v))
    if not m: raise ValueError(f"bad max_age {v!r} (use e.g. 15m, 2h, 26h, 7d)")
    return float(m.group(1)) * UNITS[m.group(2) or "s"]

def ago(sec):
    if sec is None: return "never"
    for u, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if sec >= n: return f"{sec / n:.1f}{u} ago"
    return f"{int(sec)}s ago"

def load(p, default):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return default

def save(p, d):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(d, f, indent=1)
    os.replace(tmp, p)

def iso(s): return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def last_n8n_success(wid):
    q = urllib.parse.urlencode({"workflowId": wid, "status": "success", "limit": 1})
    req = urllib.request.Request(f"{N8N}/api/v1/executions?{q}", headers={"X-N8N-API-KEY": KEY, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r: data = json.load(r).get("data", [])
    if not data: return None
    e = data[0]; return iso(e.get("stoppedAt") or e.get("startedAt"))

def evaluate(c, now, pings):
    """Return (ok, detail) for one heartbeat."""
    t, target = c.get("type"), str(c.get("target", c.get("name")))
    if t == "url":
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "TaskToAgent-heartbeat-watchdog/1.0"})
            with urllib.request.urlopen(req, timeout=int(c.get("timeout", 20))) as r: return True, f"HTTP {r.status}"
        except urllib.error.HTTPError as e: return False, f"HTTP {e.code}"
        except Exception as e: return False, f"unreachable ({type(e).__name__}: {e})"[:200]
    limit = secs(c.get("max_age", "25h"))
    if t == "file": last = os.path.getmtime(target) if os.path.exists(target) else None
    elif t == "ping": last = pings.get(target)
    elif t == "n8n":
        if not KEY: return False, "N8N_API_KEY not set"
        try: last = last_n8n_success(target)
        except Exception as e: return False, f"n8n API error ({e})"[:200]
    else: return False, f"unknown type {t!r}"
    age = None if last is None else now - last
    return (age is not None and age <= limit), f"last success {ago(age)} (limit {c.get('max_age', '25h')})"

def send(text):
    if DRY or (not WEBHOOK and not os.getenv("EMAIL_TO")): print(text); return
    if WEBHOOK:
        body = json.dumps({"username": "Heartbeat watchdog", "content": text[:1990], "allowed_mentions": {"parse": []}}).encode()
        for attempt in range(3):
            try:
                urllib.request.urlopen(urllib.request.Request(WEBHOOK, body, {"Content-Type": "application/json", "User-Agent": "TaskToAgent-heartbeat-watchdog/1.0"}), timeout=20).read(); break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 2: raise
                time.sleep(float(e.headers.get("Retry-After", "2")))
    if os.getenv("EMAIL_TO"):
        m = EmailMessage(); m["Subject"] = text.splitlines()[0][:120]; m["To"] = os.environ["EMAIL_TO"]
        m["From"] = (os.getenv("EMAIL_FROM") or (os.getenv("SMTP_USER") or os.environ["EMAIL_TO"])); m.set_content(text)
        with smtplib.SMTP((os.getenv("SMTP_HOST") or "smtp.gmail.com"), int((os.getenv("SMTP_PORT") or "587"))) as s:
            s.starttls(context=ssl.create_default_context()); s.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")); s.send_message(m)

def check():
    checks = load(CHECKS_FILE, None)
    if checks is None and DRY and "CHECKS_FILE" not in os.environ:
        print("(dry run: no checks.json yet, using checks.example.json)"); checks = load(os.path.join(HERE, "checks.example.json"), None)
    if checks is None: sys.exit(f"No {CHECKS_FILE}. Copy checks.example.json to checks.json and edit it.")
    state, pings, now = load(STATE, {}), load(PINGS, {}), time.time()
    down, up = [], []
    for c in checks:
        name = c.get("name") or c.get("target")
        ok, detail = evaluate(c, now, pings)
        print(f"{'OK  ' if ok else 'DOWN'} {name}: {detail}")
        was = state.get(name, "up")
        if not ok and was == "up": down.append(f"🔴 {name}: {detail}")
        if ok and was == "down": up.append(f"🟢 {name} is back: {detail}")
        state[name] = "up" if ok else "down"
    if down: send("Heartbeat missing\n" + "\n".join(down))
    if up: send("Heartbeat recovered\n" + "\n".join(up))
    if not down and not up: print("no change, nothing sent")
    if not DRY: save(STATE, state)

class Ping(BaseHTTPRequestHandler):
    def _ping(self):
        m = re.fullmatch(r"/ping/([A-Za-z0-9._-]{1,64})/?", urllib.parse.urlparse(self.path).path)
        if not m: self.send_response(404); self.end_headers(); return
        token = os.getenv("PING_TOKEN")
        if token and urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("token", [""])[0] != token:
            self.send_response(403); self.end_headers(); return
        p = load(PINGS, {}); p[m.group(1)] = time.time(); save(PINGS, p)
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers(); self.wfile.write(b"ok\n")
    do_GET = do_POST = do_HEAD = _ping
    def log_message(self, *a): pass

def serve():
    host, port = (os.getenv("HOST") or "0.0.0.0"), int((os.getenv("PORT") or "8765"))
    print(f"ping receiver on http://{host}:{port}/ping/<name>" + (" (token required)" if os.getenv("PING_TOKEN") else ""))
    ThreadingHTTPServer((host, port), Ping).serve_forever()

if __name__ == "__main__":
    mode = next((a for a in sys.argv[1:] if not a.startswith("-")), "check")
    if mode == "check": check()
    elif mode == "serve": serve()
    else: sys.exit(__doc__)
