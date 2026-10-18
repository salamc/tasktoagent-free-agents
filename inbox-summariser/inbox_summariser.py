#!/usr/bin/env python3
"""TaskToAgent - Inbox summariser. Python 3.9+, standard library only.
Reads your unread emails from the last N hours over IMAP (read-only: nothing is marked as read,
moved or deleted), groups them, optionally asks an OpenAI-compatible model for a short summary
with "needs a reply" flags, and prints or emails you the result.
Offline test: python3 inbox_summariser.py --eml-dir ./sample_emails --dry-run"""
import os, sys, re, json, html, glob, ssl, imaplib, smtplib, email, urllib.request
from email import policy
from email.message import EmailMessage
from email.utils import parseaddr
from datetime import datetime, timedelta

HOURS = int((os.getenv("HOURS") or "24")); MAX = int((os.getenv("MAX_EMAILS") or "40"))
UA = {"User-Agent": "TaskToAgent-Inbox-Summariser/1.0"}

def body_text(m):
    part = m.get_body(preferencelist=("plain", "html"))
    if part is None: return ""
    t = part.get_content()
    if part.get_content_type() == "text/html": t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", t)))
    return re.sub(r"\s+", " ", t).strip()

def from_imap():
    M = imaplib.IMAP4_SSL(os.environ["IMAP_HOST"], int((os.getenv("IMAP_PORT") or "993")))
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    M.select((os.getenv("IMAP_FOLDER") or "INBOX"), readonly=True)
    since = (datetime.now() - timedelta(hours=HOURS)).strftime("%d-%b-%Y")
    _, ids = M.search(None, "UNSEEN", "SINCE", since); out = []
    for i in ids[0].split()[-MAX:]:
        _, d = M.fetch(i, "(BODY.PEEK[])")  # PEEK = don't mark as read
        out.append(email.message_from_bytes(d[0][1], policy=policy.default))
    M.logout(); return out

def from_dir(d): return [email.message_from_binary_file(open(f, "rb"), policy=policy.default) for f in sorted(glob.glob(os.path.join(d, "*.eml")))][:MAX]

NOISE = re.compile(r"(no-?reply|newsletter|notifications?|mailer|news@|marketing|digest)", re.I)

def simplify(msgs):
    return [{"from": parseaddr(m["From"] or "")[1] or str(m["From"]), "name": parseaddr(m["From"] or "")[0], "subject": str(m["Subject"] or "(no subject)"),
             "snippet": body_text(m)[:400], "bulk": bool(NOISE.search(m["From"] or "") or m["List-Unsubscribe"])} for m in msgs]

def ai(items):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return None
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    prompt = "\n".join(f"{n+1}. From {i['name']} <{i['from']}> | {i['subject']} | {i['snippet']}" for n, i in enumerate(items))
    body = {"model": (os.getenv("OPENAI_MODEL") or "gpt-4o-mini"), "messages": [
        {"role": "system", "content": "Summarise this inbox for a busy person. First 'Needs a reply' (who, what, by when), then 'FYI', then a one-line count of newsletters/notifications. Be brief. Never invent facts."},
        {"role": "user", "content": prompt}]}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer " + key, **UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception as e: print(f"warn: AI summary failed, using plain summary: {e}", file=sys.stderr); return None

def build(items):
    head = f"Inbox summary - {len(items)} unread email(s) in the last {HOURS}h\n\n"
    if not items: return head + "Inbox zero. Nice."
    s = ai(items)
    if s: return head + s
    people = [i for i in items if not i["bulk"]]; bulk = [i for i in items if i["bulk"]]
    out = ["From people:"] + [f"- {i['name'] or i['from']}: {i['subject']}\n  {i['snippet'][:140]}" for i in people]
    out += ["", f"Newsletters / notifications ({len(bulk)}):"] + [f"- {i['name'] or i['from']}: {i['subject']}" for i in bulk]
    return head + "\n".join(out)

def deliver(text):
    to = os.getenv("EMAIL_TO")
    if "--dry-run" in sys.argv or not to or not os.getenv("SMTP_HOST"): print(text); return
    m = EmailMessage(); m["Subject"] = "Your inbox summary"; m["From"] = (os.getenv("EMAIL_FROM") or (os.getenv("SMTP_USER") or os.getenv("IMAP_USER"))); m["To"] = to; m.set_content(text)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int((os.getenv("SMTP_PORT") or "587")), timeout=30) as s:
        s.starttls(context=ssl.create_default_context()); s.login((os.getenv("SMTP_USER") or os.getenv("IMAP_USER")), (os.getenv("SMTP_PASSWORD") or os.getenv("IMAP_PASSWORD"))); s.send_message(m)
    print(f"summary sent to {to}")

if __name__ == "__main__":
    d = sys.argv[sys.argv.index("--eml-dir") + 1] if "--eml-dir" in sys.argv else None
    deliver(build(simplify(from_dir(d) if d else from_imap())))
