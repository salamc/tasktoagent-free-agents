#!/usr/bin/env python3
"""TaskToAgent - n8n error alert + nightly backup. Python 3.9+, standard library only (plus git for backups).
  backup : exports every workflow through the n8n public API into BACKUP_DIR (one JSON file each),
           then git-commits the changes and pushes if the repo has a remote. Credentials are never
           exported (the n8n API doesn't return their secrets, and we don't ask for them).
  check  : looks for failed executions since the last check and alerts Discord and/or email.
Usage: python3 n8n_backup_and_alert.py backup | check   (add --dry-run to only print)"""
import os, sys, re, json, ssl, time, smtplib, subprocess, urllib.request, urllib.parse, urllib.error
from email.message import EmailMessage
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
N8N = (os.getenv("N8N_URL") or "http://localhost:5678").rstrip("/")
KEY = os.getenv("N8N_API_KEY", "")
BACKUP_DIR = (os.getenv("BACKUP_DIR") or os.path.join(HERE, "n8n-backup"))
STATE = (os.getenv("STATE_FILE") or os.path.join(HERE, "n8n_alert_state.json"))
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
DRY = "--dry-run" in sys.argv
VOLATILE = ("updatedAt", "createdAt", "versionId", "activeVersionId", "triggerCount", "shared", "homeProject", "scopes", "activeVersion", "meta")

def api(path, params=None):
    url = f"{N8N}/api/v1/{path}" + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"X-N8N-API-KEY": KEY, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)

def paged(path, params=None):
    params = dict(params or {}, limit=100)
    while True:
        d = api(path, params); yield from d.get("data", [])
        if not d.get("nextCursor"): return
        params["cursor"] = d["nextCursor"]

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "workflow"

def git(*a): return subprocess.run(["git", "-C", BACKUP_DIR, *a], capture_output=True, text=True)

def backup():
    wfs = list(paged("workflows"))
    os.makedirs(BACKUP_DIR, exist_ok=True)
    keep = set()
    for w in wfs:
        clean = {k: v for k, v in w.items() if k not in VOLATILE}  # stable files = clean git diffs
        fn = f"{slug(w.get('name', ''))}--{w['id']}.json"; keep.add(fn)
        if DRY: print("would write", fn); continue
        with open(os.path.join(BACKUP_DIR, fn), "w", encoding="utf-8") as f: json.dump(clean, f, indent=2, ensure_ascii=False, sort_keys=True); f.write("\n")
    if DRY: print(f"{len(wfs)} workflow(s) found (dry run, nothing written)"); return
    for fn in os.listdir(BACKUP_DIR):  # workflows deleted in n8n disappear from the latest commit (git history keeps them)
        if fn.endswith(".json") and fn not in keep: os.remove(os.path.join(BACKUP_DIR, fn))
    if not os.path.isdir(os.path.join(BACKUP_DIR, ".git")): git("init", "-q"); print("initialised git repo in", BACKUP_DIR)
    git("add", "-A")
    if git("status", "--porcelain").stdout.strip(): commit(len(wfs))
    else: print(f"{len(wfs)} workflow(s), no changes since last backup")
    if git("remote").stdout.strip():  # also pushes commits a previous run couldn't push
        p = git("push", "-q", "origin", "HEAD")
        print("pushed to remote" if p.returncode == 0 else "warn: push failed: " + p.stderr.strip())

def commit(n):
    msg = f"n8n backup {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC ({n} workflows)"
    r = git("-c", "user.name=n8n-backup", "-c", "user.email=n8n-backup@localhost", "commit", "-q", "-m", msg)
    if r.returncode: sys.exit("git commit failed: " + r.stderr)
    print("committed:", msg)

def alert(lines):
    text = "🚨 n8n: failed executions\n" + "\n".join(lines)
    if DRY or (not WEBHOOK and not os.getenv("EMAIL_TO")): print(text); return
    if WEBHOOK:
        body = json.dumps({"username": "n8n alerts", "content": text[:1990], "allowed_mentions": {"parse": []}}).encode()
        urllib.request.urlopen(urllib.request.Request(WEBHOOK, body, {"Content-Type": "application/json", "User-Agent": "TaskToAgent-n8n-alert/1.0"}), timeout=20).read()
    if os.getenv("EMAIL_TO"):
        m = EmailMessage(); m["Subject"] = f"n8n: {len(lines)} failed execution(s)"; m["To"] = os.environ["EMAIL_TO"]
        m["From"] = (os.getenv("EMAIL_FROM") or (os.getenv("SMTP_USER") or os.environ["EMAIL_TO"])); m.set_content(text)
        with smtplib.SMTP((os.getenv("SMTP_HOST") or "smtp.gmail.com"), int((os.getenv("SMTP_PORT") or "587"))) as s:
            s.starttls(context=ssl.create_default_context()); s.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")); s.send_message(m)
    print(f"alerted: {len(lines)} failure(s)")

def check():
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    last = int(st.get("last_id", 0)); names = {w["id"]: w.get("name") for w in paged("workflows")}
    fails = [e for e in paged("executions", {"status": "error"}) if int(e["id"]) > last]
    if not st:  # first run: remember old failures instead of alerting about all of them
        fails_ids = [int(e["id"]) for e in fails]
        print(f"first run: {len(fails)} older failure(s) remembered, you'll be alerted about new ones")
        if not DRY: json.dump({"last_id": max([0] + fails_ids), "checked": datetime.now(timezone.utc).isoformat()}, open(STATE, "w"))
        return
    if fails:
        lines = [f"• {names.get(e.get('workflowId'), e.get('workflowId'))}: execution {e['id']} at {e.get('startedAt','?')[:19].replace('T',' ')} UTC  {N8N}/workflow/{e.get('workflowId')}/executions/{e['id']}" for e in sorted(fails, key=lambda e: int(e["id"]))[:20]]
        if len(fails) > 20: lines.append(f"…and {len(fails)-20} more")
        alert(lines)
    else: print("no new failures")
    if not DRY: json.dump({"last_id": max([last] + [int(e["id"]) for e in fails]), "checked": datetime.now(timezone.utc).isoformat()}, open(STATE, "w"))

if __name__ == "__main__":
    if not KEY: sys.exit("Set N8N_API_KEY (n8n: Settings > n8n API > Create an API key)")
    mode = next((a for a in sys.argv[1:] if not a.startswith("-")), "")
    if mode == "backup": backup()
    elif mode == "check": check()
    else: sys.exit(__doc__)
