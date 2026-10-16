#!/usr/bin/env python3
"""TaskToAgent - Unanswered email nudger. Python 3.9+, standard library only.
Lists emails YOU sent that got no reply after N days, so you can follow up.
It never sends anything to the people you emailed. It only prints the list, or emails it to you.
Read-only over IMAP: folders are opened read-only and only headers are fetched with BODY.PEEK.
Offline test: python3 unanswered_email_nudger.py --eml-dir sample_emails --dry-run
(sample_emails/sent/*.eml and sample_emails/inbox/*.eml)"""
import os, sys, re, glob, imaplib, smtplib, ssl, email
from email import policy
from email.message import EmailMessage
from email.utils import parseaddr, getaddresses, parsedate_to_datetime
from datetime import datetime, timedelta, timezone

DAYS = int(os.getenv("DAYS", "3"))                # no reply after this many days -> listed
LOOKBACK = int(os.getenv("LOOKBACK_DAYS", "21"))  # ignore sent mail older than this
ME = [a.strip().lower() for a in os.getenv("MY_ADDRESSES", os.getenv("IMAP_USER", "")).split(",") if a.strip()]
SKIP = re.compile(os.getenv("SKIP_RECIPIENTS", r"no-?reply|notifications?@|mailer-daemon|calendar|invite"), re.I)
SKIP_SUBJ = re.compile(os.getenv("SKIP_SUBJECTS", r"^(accepted|declined|automatic reply|out of office)"), re.I)
HDRS = "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID IN-REPLY-TO REFERENCES FROM TO CC SUBJECT DATE)])"

def norm_subj(s): return re.sub(r"^\s*((re|fw|fwd|aw|tr|sv)\s*:\s*)+", "", s or "", flags=re.I).strip().lower()

def info(m):
    try: d = parsedate_to_datetime(m["Date"]); d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: d = datetime.now(timezone.utc)
    refs = set(re.findall(r"<[^>]+>", f"{m['In-Reply-To'] or ''} {m['References'] or ''}"))
    return {"id": (m["Message-ID"] or "").strip(), "refs": refs, "from": parseaddr(str(m["From"] or ""))[1].lower(),
            "to": [a.lower() for _, a in getaddresses([str(m["To"] or ""), str(m["Cc"] or "")]) if a],
            "subject": str(m["Subject"] or "(no subject)"), "date": d}

def imap_folder(M, folder, since):
    typ, _ = M.select(f'"{folder}"' if " " in folder else folder, readonly=True)
    if typ != "OK": print(f"warn: can't open folder {folder!r}", file=sys.stderr); return []
    _, ids = M.search(None, "SINCE", since.strftime("%d-%b-%Y")); out = []
    for i in ids[0].split():
        _, d = M.fetch(i, HDRS)
        if d and isinstance(d[0], tuple): out.append(info(email.message_from_bytes(d[0][1], policy=policy.default)))
    return out

def find_sent(M):
    if os.getenv("SENT_FOLDER"): return os.environ["SENT_FOLDER"]
    _, boxes = M.list()
    for b in boxes or []:
        line = b.decode(errors="ignore")
        if "\\Sent" in line: return line.rsplit(' "/" ', 1)[-1].rsplit(' "." ', 1)[-1].strip().strip('"')
    return "Sent"

def from_imap(since):
    M = imaplib.IMAP4_SSL(os.environ["IMAP_HOST"], int(os.getenv("IMAP_PORT", "993")))
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    sent = imap_folder(M, find_sent(M), since)
    inbox = []
    for f in os.getenv("REPLY_FOLDERS", "INBOX").split(","): inbox += imap_folder(M, f.strip(), since)
    M.logout(); return sent, inbox

def from_dir(d):
    rd = lambda sub: [info(email.message_from_binary_file(open(f, "rb"), policy=policy.default)) for f in sorted(glob.glob(os.path.join(d, sub, "*.eml")))]
    return rd("sent"), rd("inbox")

def unanswered(sent, inbox, now):
    out = []
    for s in sent:
        if now - s["date"] < timedelta(days=DAYS) or SKIP_SUBJ.search(s["subject"]): continue
        rcpts = [a for a in s["to"] if a not in ME and not SKIP.search(a)]
        if not rcpts: continue
        replied = False
        for r in inbox + sent:  # a later message in the thread from them (or you already followed up)
            if r is s or r["date"] <= s["date"]: continue
            if s["id"] and s["id"] in r["refs"]: replied = True; break
            if r["from"] in rcpts and norm_subj(r["subject"]) == norm_subj(s["subject"]): replied = True; break
        if not replied: out.append({**s, "rcpts": rcpts, "age": (now - s["date"]).days})
    # keep only the latest unanswered message per thread
    best = {}
    for u in out:
        k = (norm_subj(u["subject"]), tuple(u["rcpts"]))
        if k not in best or u["date"] > best[k]["date"]: best[k] = u
    return sorted(best.values(), key=lambda u: -u["age"])

def report(items):
    if not items: return f"No unanswered emails older than {DAYS} days. Nothing to chase."
    lines = [f"{len(items)} sent email(s) with no reply after {DAYS}+ days:\n"]
    for u in items: lines.append(f"- {u['age']}d ago -> {', '.join(u['rcpts'])}\n  {u['subject']}  (sent {u['date']:%a %d %b})")
    lines.append("\nNothing was sent to anyone. Follow up yourself when it makes sense.\n-- TaskToAgent: https://tasktoagent.com/agents/unanswered-email-nudger/")
    return "\n".join(lines)

def main():
    now = datetime.now(timezone.utc); since = now - timedelta(days=LOOKBACK)
    if "--eml-dir" in sys.argv: sent, inbox = from_dir(sys.argv[sys.argv.index("--eml-dir") + 1])
    else:
        sent, inbox = from_imap(since)
        sent = [s for s in sent if s["date"] >= since]
    text = report(unanswered(sent, inbox, now))
    to = os.getenv("EMAIL_TO")
    if "--dry-run" in sys.argv or not to: print(text); return
    msg = EmailMessage(); msg["Subject"] = "Emails waiting for a reply"; msg["From"] = os.getenv("EMAIL_FROM", os.getenv("SMTP_USER", os.getenv("IMAP_USER", to))); msg["To"] = to
    msg.set_content(text)
    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(os.getenv("SMTP_USER", os.getenv("IMAP_USER", "")), os.getenv("SMTP_PASSWORD", os.getenv("IMAP_PASSWORD", "")))
        s.send_message(msg)
    print(f"report emailed to {to} (only to you)")

if __name__ == "__main__": main()
