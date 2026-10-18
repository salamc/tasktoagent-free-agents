#!/usr/bin/env python3
"""TaskToAgent - Website change alert. Python 3.9+, standard library only.
Checks web pages on a schedule and tells you on Discord, Telegram, Slack or email when they change:
the lines that were added and removed, or only when a phrase appears or disappears ("In stock", "Sold out").
No bot or server to host: run it every 15-60 minutes with cron.
  python3 website_change_alert.py --demo      # no accounts needed: shows what an alert looks like
  python3 website_change_alert.py --dry-run   # real pages, prints instead of posting, saves nothing
Page: https://tasktoagent.com/agents/website-change-alert/ · MIT licence"""
import gzip, hashlib, html.parser, json, os, re, smtplib, ssl, sys, time, urllib.error, urllib.request, zlib
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
WATCHES_FILE = os.getenv("WATCHES_FILE") or os.path.join(HERE, "watches.json")
STATE = os.getenv("STATE_FILE") or os.path.join(HERE, "website_change_state.json")
DISCORD = os.getenv("DISCORD_WEBHOOK_URL", "")
TG_TOKEN, TG_CHAT = os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", "")
TG_API = os.getenv("TELEGRAM_API_URL") or "https://api.telegram.org"
SLACK = os.getenv("SLACK_WEBHOOK_URL", "")
EMAIL_TO, SMTP_HOST = os.getenv("EMAIL_TO", ""), os.getenv("SMTP_HOST", "")
SMTP_PORT, SMTP_USER, SMTP_PASS = int(os.getenv("SMTP_PORT") or 465), os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")
FAIL_ALERT = int(os.getenv("FAIL_ALERT_AFTER") or 3)  # tell you once when a page can't be fetched this many runs in a row
DEMO, DRY = "--demo" in sys.argv, "--dry-run" in sys.argv
UA = os.getenv("USER_AGENT") or "Mozilla/5.0 (compatible; TaskToAgent-Website-Change-Alert/1.0; +https://tasktoagent.com/agents/website-change-alert/)"
MAX_LINES = 12

class Text(html.parser.HTMLParser):
    """Visible text of a page, one line per block (paragraph, heading, list item, table cell...)."""
    BLOCK = {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "header", "footer", "option", "dt", "dd", "blockquote", "pre", "button", "label", "title"}
    SKIP = {"script", "style", "noscript", "template", "svg", "head"}
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out, self.skip = [""], 0
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP: self.skip += 1
        elif tag in self.BLOCK: self.out.append("")
    def handle_endtag(self, tag):
        if tag in self.SKIP: self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK: self.out.append("")
    def handle_data(self, d):
        if not self.skip: self.out[-1] += d
    def lines(self):
        return [l for l in (" ".join(x.split()) for x in self.out) if l]

def page_lines(raw, w):
    p = Text(); p.feed(raw); lines = p.lines()
    text = "\n".join(lines)
    if w.get("start") and w["start"] in text: text = text.split(w["start"], 1)[1]
    if w.get("end") and w["end"] in text: text = text.split(w["end"], 1)[0]
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if w.get("ignore"):
        rx = re.compile(w["ignore"], re.I)
        lines = [l for l in (rx.sub("", l).strip() for l in lines) if l]
    return lines

def fetch(url, tries=2):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "en,*;q=0.5"})
            with urllib.request.urlopen(req, timeout=30) as r:
                cs = r.headers.get_content_charset() or "utf-8"
                raw, enc = r.read(5_000_000), (r.headers.get("Content-Encoding") or "").lower()
                if "gzip" in enc or raw[:2] == b"\x1f\x8b": raw = gzip.decompress(raw)  # some servers gzip even when not asked
                elif "deflate" in enc: raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                return raw.decode(cs, "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and i < tries - 1:
                try: wait = float(e.headers.get("Retry-After") or 10)
                except ValueError: wait = 10
                time.sleep(min(wait, 60)); continue
            raise

def post(url, payload, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                try:
                    j = json.loads(e.read() or b"{}")
                    wait = float(j.get("retry_after") or (j.get("parameters") or {}).get("retry_after") or e.headers.get("Retry-After") or 2)
                except Exception: wait = 2
                time.sleep(min(wait, 30)); continue
            raise

def send(subject, body):
    """Send to every configured place. One failing doesn't block the others; raises only if all failed."""
    text = f"{subject}\n{body}"
    targets = []
    if DISCORD: targets.append(("Discord", lambda: post(DISCORD, {"username": "Website Change Alert", "content": text[:1990], "allowed_mentions": {"parse": []}})))
    if TG_TOKEN and TG_CHAT: targets.append(("Telegram", lambda: post(f"{TG_API}/bot{TG_TOKEN}/sendMessage", {"chat_id": TG_CHAT, "text": text[:4000], "disable_web_page_preview": True})))
    if SLACK: targets.append(("Slack", lambda: post(SLACK, {"text": text[:3900]})))
    if EMAIL_TO and SMTP_HOST: targets.append(("Email", lambda: mail(subject, body)))
    ok, bad = 0, []
    for name, fn in targets:
        try: fn(); ok += 1
        except Exception as e: bad.append(name); print(f"warn: {name} failed: {e}", file=sys.stderr)
    if targets and not ok: raise RuntimeError(f"every destination failed ({', '.join(bad)}); will retry next run")

def mail(subject, body):
    m = EmailMessage(); m["Subject"], m["From"], m["To"] = subject, SMTP_USER or EMAIL_TO, EMAIL_TO; m.set_content(body)
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context(), timeout=30) as s:
            if SMTP_USER: s.login(SMTP_USER, SMTP_PASS)
            s.send_message(m)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls(context=ssl.create_default_context())
            if SMTP_USER: s.login(SMTP_USER, SMTP_PASS)
            s.send_message(m)

def has(lines, phrase): return phrase.lower() in "\n".join(lines).lower()

def check(w, old, raw):
    """Returns (alert or None, new state for this watch)."""
    lines = page_lines(raw, w)
    h = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    new = {"hash": h, "lines": lines[:3000], "fails": 0}
    name, url = w.get("name") or w["url"], w["url"]
    if w.get("appears") or w.get("disappears"):
        hit = (has(lines, w["appears"]) if w.get("appears") else True) and (not has(lines, w["disappears"]) if w.get("disappears") else True)
        new["hit"] = hit
        if "hit" not in old: return None, new  # first run: just remember
        if hit and not old["hit"]:
            why = " and ".join(x for x in ((f'"{w["appears"]}" is now on the page' if w.get("appears") else ""), (f'"{w["disappears"]}" is gone' if w.get("disappears") else "")) if x)
            return (f"🔔 {name}: {why}", url), new
        return None, new
    if "hash" not in old or old["hash"] == h: return None, new
    before, after = set(old.get("lines", [])), set(lines)  # lines that only moved (ranking lists, reordered menus) don't count
    added = list(dict.fromkeys(l for l in lines if l not in before))
    removed = list(dict.fromkeys(l for l in old.get("lines", []) if l not in after))
    if not added and not removed: return None, new
    body = []
    for sign, xs in (("+", added), ("-", removed)):
        body += [f"{sign} {x[:200]}" for x in xs[:MAX_LINES]]
        if len(xs) > MAX_LINES: body.append(f"{sign} ...and {len(xs) - MAX_LINES} more")
    return (f"🔔 {name} changed ({len(added)} added, {len(removed)} removed)", url + "\n" + "\n".join(body)), new

def load(path, default):
    try: return json.load(open(path))
    except OSError: return default
    except ValueError as e: sys.exit(f"{path} is not valid JSON: {e}")

DEMO_WATCHES = [{"name": "Example product page", "url": "https://shop.example.com/keyboard", "appears": "In stock"},
                {"name": "Example changelog", "url": "https://example.com/changelog", "ignore": r"Updated \d+ minutes ago"}]
DEMO_PAGES = {
    "https://shop.example.com/keyboard": ["<h1>Keyboard</h1><p>Sold out</p><p>$89</p>", "<h1>Keyboard</h1><p>In stock</p><p>$79</p>"],
    "https://example.com/changelog": ["<h2>v2.1</h2><p>Faster sync</p><p>Updated 3 minutes ago</p>", "<h2>v2.2</h2><p>Dark mode</p><h2>v2.1</h2><p>Faster sync</p><p>Updated 9 minutes ago</p>"]}

def main():
    if DEMO:
        watches = DEMO_WATCHES
    else:
        watches = load(WATCHES_FILE, None)
        if watches is None and os.getenv("WATCH_URL"):
            watches = [{"url": os.environ["WATCH_URL"], "appears": os.getenv("WATCH_APPEARS", ""), "disappears": os.getenv("WATCH_DISAPPEARS", ""), "ignore": os.getenv("WATCH_IGNORE", "")}]
        if not watches: sys.exit(f"No pages to watch. Copy watches.example.json to watches.json (or set WATCH_URL). Try `python3 {os.path.basename(__file__)} --demo` first.")
    posting = not (DEMO or DRY) and (DISCORD or (TG_TOKEN and TG_CHAT) or SLACK or (EMAIL_TO and SMTP_HOST))
    if not (DEMO or DRY) and not posting: print("note: no Discord/Telegram/Slack/email set, alerts are only printed", file=sys.stderr)
    state = {} if DEMO else load(STATE, {})
    changed = 0
    try:
        for w in watches:
            key = w.get("name") or w["url"]; old = state.get(key, {})
            if DEMO:
                _, old = check(w, {}, DEMO_PAGES[w["url"]][0]); raw = DEMO_PAGES[w["url"]][1]
            else:
                try: raw = fetch(w["url"])
                except Exception as e:
                    old = dict(old, fails=old.get("fails", 0) + 1); state[key] = old
                    print(f"warn: {key}: {e}", file=sys.stderr)
                    if old["fails"] == FAIL_ALERT:
                        msg = (f"⚠️ {key}: can't load the page ({FAIL_ALERT} checks in a row)", f"{w['url']}\nLast error: {e}")
                        try:
                            if posting: send(*msg)
                            else: print("\n".join(msg) + "\n")
                        except RuntimeError as e2: print(f"warn: {key}: {e2}", file=sys.stderr); state[key] = dict(old, fails=FAIL_ALERT - 1)
                    continue
            alert, new = check(w, old, raw)
            if alert:
                changed += 1
                if posting:
                    try: send(*alert)
                    except RuntimeError as e: print(f"warn: {key}: {e}", file=sys.stderr); continue  # keep old state, retry next run
                else: print("\n".join(alert) + "\n")
            state[key] = new
            if not DEMO: time.sleep(1)
    finally:  # save even if something failed later, so alerts that went out aren't repeated
        if not (DEMO or DRY): json.dump(state, open(STATE, "w"))
    print(f"{len(watches)} pages checked, {changed} changed" + ("" if posting else " (printed, nothing posted)"), file=sys.stderr)

if __name__ == "__main__":
    main()
