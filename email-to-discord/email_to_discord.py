#!/usr/bin/env python3
"""TaskToAgent - Email to Discord (also Telegram and Slack). Python 3.9+, standard library only.
Watches one or more IMAP inboxes and posts new matching emails (sender, subject, short preview)
to a Discord webhook, a Telegram chat (bot token + chat id) and/or a Slack incoming webhook.
Each inbox can have its own filters and its own destinations. Set any one or several.
Read-only: folders are opened read-only, mail is fetched with BODY.PEEK (never marked read,
moved or deleted). The first run only remembers where each inbox is, so old mail isn't flooded in.
Offline test: python3 email_to_discord.py --eml-dir sample_emails --dry-run"""
import os, sys, re, json, glob, time, html, imaplib, email, urllib.request, urllib.error
from email import policy
from email.utils import parseaddr

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = (os.getenv("STATE_FILE") or os.path.join(HERE, "email_to_discord_state.json"))
UA = {"User-Agent": "TaskToAgent-Email-To-Discord/1.0 (+https://tasktoagent.com/agents/)", "Content-Type": "application/json"}
PREVIEW = int((os.getenv("PREVIEW_CHARS") or "300"))
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or ""
TG_API = (os.getenv("TELEGRAM_API") or "https://api.telegram.org")

def inboxes():
    """INBOXES_FILE (JSON list) for several inboxes, or plain env vars for one."""
    f = os.getenv("INBOXES_FILE")
    if f: return json.load(open(f))
    return [{"name": (os.getenv("INBOX_NAME") or (os.getenv("IMAP_USER") or "inbox")), "host": os.getenv("IMAP_HOST"), "port": int((os.getenv("IMAP_PORT") or "993")),
             "user": os.getenv("IMAP_USER"), "password": os.getenv("IMAP_PASSWORD"), "folder": (os.getenv("IMAP_FOLDER") or "INBOX"),
             "webhook": os.getenv("DISCORD_WEBHOOK_URL", ""), "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
             "slack_webhook": os.getenv("SLACK_WEBHOOK_URL", ""), "from_contains": os.getenv("FROM_CONTAINS", ""),
             "subject_contains": os.getenv("SUBJECT_CONTAINS", ""), "exclude": os.getenv("EXCLUDE", "")}]

def words(v): return [w.strip().lower() for w in (v if isinstance(v, list) else str(v or "").split(",")) if w.strip()]

def match(cfg, frm, subj, body):
    fc, sc, ex = words(cfg.get("from_contains")), words(cfg.get("subject_contains")), words(cfg.get("exclude"))
    if fc and not any(w in frm.lower() for w in fc): return False
    if sc and not any(w in subj.lower() for w in sc): return False
    if ex and any(w in f"{frm} {subj} {body}".lower() for w in ex): return False
    return True

def text_of(m):
    part = m.get_body(preferencelist=("plain", "html"))
    if part is None: return ""
    t = part.get_content()
    if part.get_content_type() == "text/html": t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", t)))
    return re.sub(r"\s+", " ", t).strip()

def send(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), UA)
    for attempt in range(3):
        try: urllib.request.urlopen(req, timeout=20).read(); time.sleep(0.6); return
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                body = json.loads(e.read() or b"{}")
                wait = body.get("retry_after") or body.get("parameters", {}).get("retry_after") or e.headers.get("Retry-After") or 2
                time.sleep(float(wait) + 0.5); continue
            raise

def dests(cfg):
    """Per-inbox values win; the global env vars are the fallback."""
    d = {"discord": cfg.get("webhook") or os.getenv("DISCORD_WEBHOOK_URL") or "",
         "telegram": cfg.get("telegram_chat_id") or os.getenv("TELEGRAM_CHAT_ID") or "",
         "slack": cfg.get("slack_webhook") or os.getenv("SLACK_WEBHOOK_URL") or ""}
    if not (cfg.get("telegram_bot_token") or TG_TOKEN): d["telegram"] = ""
    return d

def post(cfg, m):
    name, addr = parseaddr(str(m["From"] or ""))
    who = (f"{name} <{addr}>" if name else addr)[:250]
    subj = str(m["Subject"] or "(no subject)"); body = text_of(m)
    atts = [p.get_filename() for p in m.iter_attachments() if p.get_filename()]
    desc = body[:PREVIEW] + ("…" if len(body) > PREVIEW else "")
    if atts: desc += f"\n📎 {', '.join(atts)[:200]}"
    d = dests(cfg)
    if not any(d.values()) or "--dry-run" in sys.argv:
        print(f"[{cfg['name']}] {name or addr}: {subj}\n   {desc[:120]}"); return
    jobs = []
    if d["discord"]: jobs.append(("Discord", d["discord"], {"username": "Email to Discord", "allowed_mentions": {"parse": []},
        "embeds": [{"title": subj[:250], "description": desc[:4000] or "(empty)", "color": 0x5865F2,
                    "author": {"name": who}, "footer": {"text": f"📬 {cfg['name']}"[:200]}}]}))
    if d["telegram"]:
        tok = cfg.get("telegram_bot_token") or TG_TOKEN
        jobs.append(("Telegram", f"{TG_API}/bot{tok}/sendMessage", {"chat_id": d["telegram"], "disable_web_page_preview": True, "parse_mode": "HTML",
            "text": f"📬 <b>{html.escape(subj[:250])}</b>\nFrom: {html.escape(who)}\n\n{html.escape(desc[:3500])}\n<i>{html.escape(cfg['name'][:100])}</i>"}))
    if d["slack"]:
        esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        jobs.append(("Slack", d["slack"], {"text": f"📬 *{esc(subj[:250])}*\nFrom: {esc(who)}\n>{esc(desc[:2500]).replace(chr(10), chr(10) + '>')}\n_{esc(cfg['name'][:100])}_"}))
    ok = 0
    for label, url, payload in jobs:
        try: send(url, payload); ok += 1
        except Exception as e: print(f"warn: [{cfg['name']}] {label}: {e}", file=sys.stderr)
    if not ok: raise RuntimeError("every destination failed; this email will be retried next run")

def run_imap(cfg, state):
    key = f"{cfg['user']}@{cfg['host']}/{cfg.get('folder', 'INBOX')}"
    M = imaplib.IMAP4_SSL(cfg["host"], int(cfg.get("port", 993))); M.login(cfg["user"], cfg["password"])
    M.select(cfg.get("folder", "INBOX"), readonly=True)
    _, v = M.response("UIDVALIDITY"); validity = (v[0] or b"0").decode() if v and v[0] else "0"
    st = state.get(key)
    _, data = M.uid("search", None, "ALL"); uids = [int(u) for u in data[0].split()]
    if not st or st.get("validity") != validity:
        state[key] = {"validity": validity, "last": max(uids or [0])}
        print(f"[{cfg['name']}] first run: remembered {len(uids)} existing email(s), will post only new ones from now on"); M.logout(); return 0
    n = 0
    for u in [u for u in uids if u > st["last"]][:int((os.getenv("MAX_PER_RUN") or "20"))]:
        _, d = M.uid("fetch", str(u), "(BODY.PEEK[])")
        m = email.message_from_bytes(d[0][1], policy=policy.default)
        if match(cfg, str(m["From"] or ""), str(m["Subject"] or ""), text_of(m)): post(cfg, m); n += 1
        st["last"] = u
    M.logout(); return n

def main():
    if "--eml-dir" in sys.argv:  # offline test: treat every sample email as new
        cfg = {**inboxes()[0], "name": "sample"}
        for f in sorted(glob.glob(os.path.join(sys.argv[sys.argv.index("--eml-dir") + 1], "*.eml"))):
            m = email.message_from_binary_file(open(f, "rb"), policy=policy.default)
            if match(cfg, str(m["From"] or ""), str(m["Subject"] or ""), text_of(m)): post(cfg, m)
        return
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    total = 0
    for cfg in inboxes():
        try: total += run_imap(cfg, state)
        except Exception as e: print(f"warn: [{cfg.get('name')}] {e}", file=sys.stderr)
        json.dump(state, open(STATE, "w"), indent=1)
    print(f"posted {total} email(s)")

if __name__ == "__main__": main()
