#!/usr/bin/env python3
"""TaskToAgent - Email attachment saver. Python 3.9+, standard library only.
Finds emails with attachments over IMAP (read-only: nothing is marked read, moved or deleted) and saves
the attachments into folders like  saved/2026-10/invoices@shop.com/invoice.pdf .
Point SAVE_DIR at a Dropbox / Google Drive / OneDrive synced folder to get them in the cloud.
Skips duplicates (by SHA-256), filters by extension and sender. Offline test: --eml-dir ./sample_emails"""
import os, sys, re, glob, json, email, imaplib, hashlib
from email import policy
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timedelta

SAVE_DIR = os.path.expanduser((os.getenv("SAVE_DIR") or "./saved_attachments"))
EXTS = {e.strip().lower().lstrip(".") for e in (os.getenv("EXTENSIONS") or "pdf,png,jpg,jpeg,docx,xlsx,csv,zip").split(",") if e.strip()}
FROM_FILTER = [f.strip().lower() for f in os.getenv("FROM_CONTAINS", "").split(",") if f.strip()]
DAYS = int((os.getenv("DAYS") or "7"))
INDEX = os.path.join(SAVE_DIR, ".saved_hashes.json")

def safe(name): return re.sub(r"[^\w.@+-]+", "_", name).strip("._")[:120] or "file"

def messages():
    if "--eml-dir" in sys.argv:
        for f in sorted(glob.glob(os.path.join(sys.argv[sys.argv.index("--eml-dir") + 1], "*.eml"))):
            yield email.message_from_binary_file(open(f, "rb"), policy=policy.default)
        return
    M = imaplib.IMAP4_SSL(os.environ["IMAP_HOST"], int((os.getenv("IMAP_PORT") or "993")))
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"]); M.select((os.getenv("IMAP_FOLDER") or "INBOX"), readonly=True)
    _, ids = M.search(None, "SINCE", (datetime.now() - timedelta(days=DAYS)).strftime("%d-%b-%Y"))
    for i in ids[0].split():
        _, d = M.fetch(i, "(BODY.PEEK[])"); yield email.message_from_bytes(d[0][1], policy=policy.default)
    M.logout()

def main():
    dry = "--dry-run" in sys.argv
    if not dry: os.makedirs(SAVE_DIR, exist_ok=True)
    hashes = set(json.load(open(INDEX))) if os.path.exists(INDEX) else set(); saved = skipped = 0
    for m in messages():
        sender = (parseaddr(m["From"] or "")[1] or "unknown").lower()
        if FROM_FILTER and not any(f in sender for f in FROM_FILTER): continue
        try: when = parsedate_to_datetime(m["Date"])
        except Exception: when = datetime.now()
        for part in m.iter_attachments():
            name = part.get_filename() or "attachment"; ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if EXTS and ext not in EXTS: continue
            data = part.get_payload(decode=True) or b""; h = hashlib.sha256(data).hexdigest()
            if h in hashes: skipped += 1; continue
            folder = os.path.join(SAVE_DIR, f"{when:%Y-%m}", safe(sender)); path = os.path.join(folder, safe(name))
            base, dot = os.path.splitext(path); n = 1
            while os.path.exists(path): path = f"{base}-{n}{dot}"; n += 1
            print(("would save " if dry else "saved ") + os.path.relpath(path, SAVE_DIR) + f" ({len(data)} bytes)")
            if not dry:
                os.makedirs(folder, exist_ok=True); open(path, "wb").write(data)
            hashes.add(h)
            saved += 1
    if not dry: json.dump(sorted(hashes), open(INDEX, "w"))
    print(f"done: {saved} saved, {skipped} duplicate(s) skipped")

if __name__ == "__main__": main()
