#!/usr/bin/env python3
"""TaskToAgent - Inbox summariser. Python 3.9+, standard library only.
Reads your unread emails from the last N hours over IMAP (read-only: nothing is marked as read,
moved or deleted), separates people from newsletters, groups replies into conversations, flags emails
that look like they need a reply, optionally asks an OpenAI-compatible model for a short summary
(only people's emails are sent to it), and prints or emails you the result.
Offline test: python3 inbox_summariser.py --eml-dir ./sample_emails --dry-run"""
import os, sys, re, json, html, glob, ssl, imaplib, smtplib, email, urllib.request
from email import policy
from email.message import EmailMessage
from email.utils import parseaddr
from datetime import datetime, timedelta

HOURS = int((os.getenv("HOURS") or "24")); MAX = int((os.getenv("MAX_EMAILS") or "40"))
UA = {"User-Agent": "TaskToAgent-Inbox-Summariser/1.1"}

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

NOISE = re.compile(r"(no-?reply|do-?not-?reply|newsletter|notifications?|mailer|news@|marketing|digest|updates@)", re.I)
def addrs(v): return [x.strip().lower() for x in (v or "").split(",") if x.strip()]
PEOPLE = addrs(os.getenv("PEOPLE")); BULK = addrs(os.getenv("BULK"))  # addresses or @domains that override the guess
ASK = re.compile(r"\?|\b(can|could|would|will) you\b|\bplease\b|\blet me know\b|\bby (mon|tues|wednes|thurs|fri|satur|sun)day\b|\b(asap|urgent|deadline|tomorrow|eod|rsvp)\b", re.I)
PREFIX = re.compile(r"^\s*((re|fwd?|fw|aw|wg|tr|sv|vs|rv|antw)\s*(\[\d+\])?\s*:\s*)+", re.I)

def listed(addr, lst): return any(addr == x or (x.startswith("@") and addr.endswith(x)) for x in lst)

def is_bulk(m, addr):
    if listed(addr, PEOPLE): return False
    if listed(addr, BULK): return True
    prec = str(m["Precedence"] or "").lower(); auto = str(m["Auto-Submitted"] or "no").lower()
    return bool(NOISE.search(addr) or m["List-Unsubscribe"] or m["List-Id"] or prec in ("bulk", "list", "junk") or auto != "no")

def ids(v): return re.findall(r"<[^<>\s]+>", str(v or ""))

def simplify(msgs):
    out = []
    for m in msgs:
        name, addr = parseaddr(str(m["From"] or "")); addr = addr.lower() or str(m["From"] or "")
        refs = ids(m["References"]) or ids(m["In-Reply-To"])
        subj = str(m["Subject"] or "(no subject)"); text = body_text(m)
        out.append({"from": addr, "name": name, "subject": subj, "snippet": text[:400], "bulk": is_bulk(m, addr),
                    "ask": bool(ASK.search(subj + " " + text[:600])), "root": refs[0] if refs else (ids(m["Message-ID"]) or [None])[0],
                    "topic": PREFIX.sub("", subj).strip().lower()})
    return out

def threads(items):
    """Group people's emails into conversations: same root Message-ID (References/In-Reply-To), or same subject without Re:/Fwd:."""
    groups, index = [], {}
    for i in items:
        keys = [k for k in (i["root"] and "id:" + i["root"], len(i["topic"]) >= 4 and "s:" + i["topic"]) if k]
        g = next((index[k] for k in keys if k in index), None)
        if g is None: g = []; groups.append(g)
        g.append(i)
        for k in keys: index.setdefault(k, g)
    return groups

def label(g):
    names = []
    for i in g:
        n = i["name"] or i["from"]
        if n not in names: names.append(n)
    return ", ".join(names) + (f" ({len(g)} messages)" if len(g) > 1 else "")

def ai(convos, bulk):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return None
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    lines = [f"{n+1}. {g[-1]['subject']} | " + " / ".join(f"{i['name'] or i['from']}: {i['snippet'][:300]}" for i in g[-3:]) for n, g in enumerate(convos)]
    prompt = "Conversations with people:\n" + ("\n".join(lines) or "(none)") + f"\n\nPlus {len(bulk)} newsletters/notifications (not shown)."
    body = {"model": (os.getenv("OPENAI_MODEL") or "gpt-4o-mini"), "messages": [
        {"role": "system", "content": "Summarise this inbox for a busy person. First 'Needs a reply' (who, what, by when), then 'FYI'. One line per conversation. Be brief. Never invent facts."},
        {"role": "user", "content": prompt}]}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer " + key, **UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception as e: print(f"warn: AI summary failed, using plain summary: {e}", file=sys.stderr); return None

def bulk_lines(bulk):
    by = {}
    for i in bulk: by.setdefault(i["name"] or i["from"], []).append(i["subject"])
    return [f"- {k}" + (f" ({len(v)}): " if len(v) > 1 else ": ") + "; ".join(v[:3]) + (" ..." if len(v) > 3 else "") for k, v in sorted(by.items(), key=lambda kv: -len(kv[1]))]

def build(items):
    head = f"Inbox summary - {len(items)} unread email(s) in the last {HOURS}h\n\n"
    if not items: return head + "Inbox zero. Nice."
    bulk = [i for i in items if i["bulk"]]
    convos = sorted(threads([i for i in items if not i["bulk"]]), key=lambda g: not any(i["ask"] for i in g))
    s = ai(convos, bulk)
    if s: out = [s, ""]
    else:
        reply = [g for g in convos if any(i["ask"] for i in g)]; fyi = [g for g in convos if g not in reply]
        line = lambda g: f"- {g[-1]['subject']} - {label(g)}\n  {g[-1]['snippet'][:160]}"
        out = ([f"May need a reply ({len(reply)}):"] + [line(g) for g in reply] + [""] if reply else []) + ([f"Other emails from people ({len(fyi)}):"] + [line(g) for g in fyi] + [""] if fyi else [])
        if not convos: out = ["No emails from people.", ""]
    if bulk: out += [f"Newsletters / notifications ({len(bulk)}):"] + bulk_lines(bulk)
    return head + "\n".join(out).rstrip()

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
