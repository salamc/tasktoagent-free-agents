#!/usr/bin/env python3
"""TaskToAgent - Invoice & receipt logger. Python 3.9+, standard library only.
Finds invoice/receipt emails over IMAP (read-only, BODY.PEEK, nothing marked read or moved),
pulls date, vendor, amount and currency (best effort, from the email text and text-based PDFs),
and appends one row per invoice to a CSV file. Optional: also sends each row to a Google Sheet
through a tiny Apps Script web app (see README). Already-logged emails are skipped.
Offline test: python3 invoice_logger.py --eml-dir sample_emails --dry-run"""
import os, sys, re, csv, json, glob, zlib, imaplib, email, hashlib, urllib.request
from email import policy
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = (os.getenv("CSV_FILE") or os.path.join(HERE, "invoices.csv"))
DAYS = int((os.getenv("DAYS") or "30"))
KEYWORDS = [k.strip().lower() for k in (os.getenv("KEYWORDS") or "invoice,receipt,facture,rechnung,factura,order confirmation,payment received,your bill").split(",") if k.strip()]
FROM_CONTAINS = [k.strip().lower() for k in os.getenv("FROM_CONTAINS", "").split(",") if k.strip()]
SHEET_URL = os.getenv("SHEET_WEBHOOK_URL", "")
COLS = ["date", "vendor", "amount", "currency", "invoice_no", "subject", "from", "attachments", "source", "key"]
SYM = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "CHF": "CHF", "CA$": "CAD", "A$": "AUD"}

def pdf_text(data):
    """Best-effort text from simple, text-based PDFs (no OCR). Returns '' for scans."""
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = m.group(1)
        try: raw = zlib.decompress(raw)
        except Exception: pass
        for t in re.findall(rb"\((.*?)(?<!\\)\)\s*Tj|\[(.*?)\]\s*TJ", raw, re.S):
            s = t[0] or b"".join(re.findall(rb"\((.*?)(?<!\\)\)", t[1]))
            chunks.append(s.replace(rb"\(", b"(").replace(rb"\)", b")").decode("latin-1", "ignore"))
    return " ".join(chunks)

AMT = r"([0-9]{1,3}(?:[ ,.\u202f][0-9]{3})*(?:[.,][0-9]{2})|[0-9]+(?:[.,][0-9]{2})?)"
CUR = r"(US\$|CA\$|A\$|\$|€|£|¥|₹|USD|EUR|GBP|CHF|CAD|AUD|JPY|INR)"
TOTAL = re.compile(r"(?i)(grand total|total due|amount due|total paid|amount paid|balance due|total ttc|montant total|total|amount|charged)[^0-9$€£¥₹A-Z\n]{0,25}" + CUR + r"?\s?" + AMT + r"\s?" + CUR + "?")
ANY = re.compile(CUR + r"\s?" + AMT + "|" + AMT + r"\s?" + CUR)

def to_num(s):
    s = s.replace(" ", "").replace("\u202f", "")
    if re.search(r"[.,]\d{2}$", s): whole, dec = s[:-3], s[-2:]
    else: whole, dec = s, "00"
    return float(re.sub(r"[.,]", "", whole) + "." + dec)

def cur(c):
    c = (c or "").upper().replace("US$", "$")
    return SYM.get(c, c) if c else ""

def parse(text):
    amount, currency = "", ""
    hits = TOTAL.findall(text)
    if hits:  # prefer the last "total"-like line (usually the grand total)
        _, c1, a, c2 = hits[-1]; amount, currency = to_num(a), cur(c1 or c2)
    else:
        vals = [(to_num(m[1] or m[2]), cur(m[0] or m[3])) for m in ANY.findall(text)]
        if vals: amount, currency = max(vals)
    inv = re.search(r"(?i)(invoice|receipt|order|facture|bill)\s*(?:confirmation\s*)?(?:no\.?|number|#|n°|id)\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/]{2,})", text)
    return {"amount": f"{amount:.2f}" if amount != "" else "", "currency": currency, "invoice_no": inv.group(2) if inv else ""}

def vendor(m):
    name, addr = parseaddr(str(m["From"] or ""))
    name = re.sub(r"(?i)\b(billing|invoices?|receipts?|orders?|no-?reply|team|payments?)\b", "", name).strip(" -|·,")
    return name or (addr.split("@")[-1].split(".")[-2].capitalize() if "@" in addr else addr)

def body_text(m):
    part = m.get_body(preferencelist=("plain", "html"))
    if part is None: return ""
    t = part.get_content()
    if part.get_content_type() == "text/html": t = re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", t))
    return re.sub(r"[ \t]+", " ", t)

def is_invoice(m, atts):
    hay = f"{m['Subject'] or ''} {' '.join(n for n, _ in atts)}".lower()
    frm = str(m["From"] or "").lower()
    if FROM_CONTAINS and not any(k in frm for k in FROM_CONTAINS): return False
    return bool(FROM_CONTAINS) or any(k in hay for k in KEYWORDS)

def row(m, source):
    atts = [(p.get_filename() or "", p.get_payload(decode=True) or b"") for p in m.iter_attachments()]
    if not is_invoice(m, atts): return None
    text = (m["Subject"] or "") + "\n" + body_text(m)
    for n, data in atts:
        if n.lower().endswith(".pdf"): text += "\n" + pdf_text(data)
        elif n.lower().endswith((".txt", ".csv", ".html")): text += "\n" + data.decode("utf-8", "ignore")
    p = parse(text)
    dm = re.search(r"(?i)(?:invoice date|date of issue|issued|date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[/.]\d{1,2}[/.]\d{2,4})", text)
    try: d = dm.group(1) if dm else parsedate_to_datetime(m["Date"]).strftime("%Y-%m-%d")
    except Exception: d = ""
    key = hashlib.sha1(((m["Message-ID"] or "") + (m["Subject"] or "") + (m["Date"] or "")).encode()).hexdigest()[:16]
    return {"date": d, "vendor": vendor(m), **p, "subject": str(m["Subject"] or ""), "from": parseaddr(str(m["From"] or ""))[1],
            "attachments": "; ".join(n for n, _ in atts if n), "source": source, "key": key}

def from_imap():
    M = imaplib.IMAP4_SSL(os.environ["IMAP_HOST"], int((os.getenv("IMAP_PORT") or "993")))
    M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
    M.select((os.getenv("IMAP_FOLDER") or "INBOX"), readonly=True)
    _, ids = M.search(None, "SINCE", (datetime.now() - timedelta(days=DAYS)).strftime("%d-%b-%Y"))
    for i in ids[0].split():
        _, d = M.fetch(i, "(BODY.PEEK[])")
        yield email.message_from_bytes(d[0][1], policy=policy.default), f"imap:{i.decode()}"
    M.logout()

def from_dir(d):
    for f in sorted(glob.glob(os.path.join(d, "*.eml"))): yield email.message_from_binary_file(open(f, "rb"), policy=policy.default), os.path.basename(f)

def main():
    src = from_dir(sys.argv[sys.argv.index("--eml-dir") + 1]) if "--eml-dir" in sys.argv else from_imap()
    dry = "--dry-run" in sys.argv
    done = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f: done = {r["key"] for r in csv.DictReader(f)}
    new = []
    for m, s in src:
        try: r = row(m, s)
        except Exception as e: print(f"warn: {s}: {e}", file=sys.stderr); continue
        if r and r["key"] not in done: new.append(r); done.add(r["key"])
    for r in new: print(f"{r['date']}  {r['vendor'][:24]:24}  {r['amount'] or '?':>10} {r['currency']:3}  {r['invoice_no']}  [{r['subject'][:50]}]")
    if not new: print("no new invoices"); return
    if dry: print(f"(dry run: {len(new)} row(s) not written)"); return
    first = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        if first: w.writeheader()
        w.writerows(new)
    print(f"added {len(new)} row(s) to {CSV_FILE}")
    if SHEET_URL:
        req = urllib.request.Request(SHEET_URL, json.dumps({"rows": [[r[c] for c in COLS] for r in new]}).encode(), {"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30).read(); print("sent to Google Sheet")

if __name__ == "__main__": main()
