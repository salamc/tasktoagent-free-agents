#!/usr/bin/env python3
"""TaskToAgent - RSS to Discord (also Telegram and Slack). Python 3.9+, standard library only.
Watches RSS/Atom feeds and posts new items (optionally only those matching keywords) to a Discord webhook,
a Telegram chat (bot token + chat id) and/or a Slack incoming webhook. Set any one or several.
First run only records what's already there (no flood); later runs post what's new."""
import os, sys, json, time, html, re, urllib.request, urllib.error, xml.etree.ElementTree as ET

FEEDS = [f.strip() for f in (os.getenv("FEEDS") or "https://hnrss.org/frontpage,https://www.rockpapershotgun.com/feed").split(",") if f.strip()]
KEYWORDS = [k.strip().lower() for k in os.getenv("KEYWORDS", "").split(",") if k.strip()]  # empty = post everything
EXCLUDE = [k.strip().lower() for k in os.getenv("EXCLUDE", "").split(",") if k.strip()]  # skip items whose title or link contains any of these, e.g. -rc,beta
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")  # e.g. 123456789, -100123... for groups/channels, or @yourchannel
SLACK = os.getenv("SLACK_WEBHOOK_URL", "")
TG_API = (os.getenv("TELEGRAM_API") or "https://api.telegram.org")
STATE = (os.getenv("STATE_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_rss.json"))
MAX_PER_RUN = int((os.getenv("MAX_PER_RUN") or "10"))
TITLE_ONLY = (os.getenv("TITLE_ONLY") or "0").lower() in ("1", "true", "yes")  # match KEYWORDS in the title only, not the post text
FEED_PAUSE = float(os.getenv("FEED_PAUSE") or "3")  # seconds between feeds; Reddit answers 429 to fast back-to-back requests
UA = {"User-Agent": "TaskToAgent-RSS-to-Discord/1.0 (+https://tasktoagent.com/agents/)"}
A = "{http://www.w3.org/2005/Atom}"

def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def fetch(url):
    for attempt in range(2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt: raise
            wait = min(float(e.headers.get("Retry-After") or 15), 60)
            print(f"note: {url}: 429, retrying in {wait:.0f}s", file=sys.stderr); time.sleep(wait)

def items(url):
    root = ET.fromstring(fetch(url))
    for it in root.iter("item"):
        yield {"id": (it.findtext("guid") or it.findtext("link") or "").strip(), "title": clean(it.findtext("title")),
               "link": (it.findtext("link") or "").strip(), "text": clean(it.findtext("description"))}
    for e in root.iter(A + "entry"):
        l = e.find(A + "link[@rel='alternate']")
        if l is None: l = e.find(A + "link")
        href = l.get("href", "") if l is not None else ""
        yield {"id": (e.findtext(A + "id") or href).strip(), "title": clean(e.findtext(A + "title")), "link": href,
               "text": clean(e.findtext(A + "summary") or e.findtext(A + "content"))}

def matches(i):
    if any(x in (i["title"] + " " + i["link"]).lower() for x in EXCLUDE): return False
    hay = i["title"] if TITLE_ONLY else i["title"] + " " + i["text"]
    return not KEYWORDS or any(k in hay.lower() for k in KEYWORDS)

def send(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {**UA, "Content-Type": "application/json"})
    for attempt in range(3):
        try: urllib.request.urlopen(req, timeout=20).read(); return
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                body = json.loads(e.read() or b"{}")
                wait = body.get("retry_after") or body.get("parameters", {}).get("retry_after") or e.headers.get("Retry-After") or 2
                time.sleep(float(wait) + 0.5); continue
            raise

def post(i):
    title, link = i["title"][:200], i["link"]
    if not (WEBHOOK or (TG_TOKEN and TG_CHAT) or SLACK) or "--dry-run" in sys.argv: print(f"**{title}**\n{link}"); return
    if WEBHOOK: send(WEBHOOK, {"username": "RSS Bot", "content": f"**{title}**\n{link}", "allowed_mentions": {"parse": []}})
    if TG_TOKEN and TG_CHAT:
        send(f"{TG_API}/bot{TG_TOKEN}/sendMessage", {"chat_id": TG_CHAT, "text": f"<b>{html.escape(title)}</b>\n{html.escape(link)}", "parse_mode": "HTML"})
    if SLACK:
        t = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        send(SLACK, {"text": f"*{t}*\n{link}" if not link else f"*<{link}|{t}>*"})

def main():
    first = not os.path.exists(STATE); seen = set() if first else set(json.load(open(STATE)))
    new = []
    for n, f in enumerate(FEEDS):
        if n: time.sleep(FEED_PAUSE)
        try: new += [i for i in items(f) if i["id"] and i["id"] not in seen]
        except Exception as e: print(f"warn: {f}: {e}", file=sys.stderr)
    if first and "--post-existing" not in sys.argv and "--dry-run" not in sys.argv:
        print(f"first run: remembered {len(new)} existing item(s), nothing posted")
    else:
        hits = [i for i in new if matches(i)][:MAX_PER_RUN]
        for i in hits: post(i); time.sleep(0.6)
        print(f"{len(hits)} new matching item(s) posted")
    if "--dry-run" not in sys.argv: json.dump(sorted(seen | {i["id"] for i in new})[-5000:], open(STATE, "w"))

if __name__ == "__main__": main()
