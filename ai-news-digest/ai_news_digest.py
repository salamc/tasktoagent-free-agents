#!/usr/bin/env python3
"""TaskToAgent - AI news digest. Python 3.9+, standard library only.
Fetches AI news from public RSS/Atom feeds, keeps items from the last N hours,
optionally summarises them with any OpenAI-compatible API, then prints or emails the digest.
Config via environment variables (see README.md)."""
import os, sys, json, smtplib, ssl, html, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

FEEDS = (os.getenv("FEEDS") or ",".join([
    "https://hnrss.org/newest?q=AI+OR+LLM+OR+agent&points=50",
    "https://huggingface.co/blog/feed.xml",
    "https://simonwillison.net/atom/everything/",
    "https://openai.com/news/rss.xml",
])).split(",")
HOURS = int((os.getenv("HOURS") or "24"))
MAX_ITEMS = int((os.getenv("MAX_ITEMS") or "12"))
UA = {"User-Agent": "TaskToAgent-AI-News-Digest/1.0 (+https://tasktoagent.com/agents/)"}

def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read()

def strip(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def parse_date(s):
    if not s: return None
    try: d = parsedate_to_datetime(s)
    except Exception:
        try: d = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        except Exception: return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def parse_feed(data, source):
    root = ET.fromstring(data); out = []
    A = "{http://www.w3.org/2005/Atom}"
    for it in root.iter("item"):
        out.append(dict(title=strip(it.findtext("title")), link=(it.findtext("link") or "").strip(),
            date=parse_date(it.findtext("pubDate") or it.findtext("{http://purl.org/dc/elements/1.1/}date")),
            summary=strip(it.findtext("description"))[:300], source=source))
    for e in root.iter(A + "entry"):
        link = e.find(A + "link[@rel='alternate']")
        if link is None: link = e.find(A + "link")
        out.append(dict(title=strip(e.findtext(A + "title")), link=link.get("href") if link is not None else "",
            date=parse_date(e.findtext(A + "published") or e.findtext(A + "updated")),
            summary=strip(e.findtext(A + "summary") or e.findtext(A + "content"))[:300], source=source))
    return out

def collect():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS); items, seen = [], set()
    for url in [f.strip() for f in FEEDS if f.strip()]:
        try: got = parse_feed(fetch(url), urllib.parse.urlparse(url).netloc)
        except Exception as e: print(f"warn: {url}: {e}", file=sys.stderr); continue
        for i in got:
            if i["link"] in seen or (i["date"] and i["date"] < cutoff): continue
            seen.add(i["link"]); items.append(i)
    items.sort(key=lambda i: i["date"] or cutoff, reverse=True)
    return items[:MAX_ITEMS]

def ai_summary(items):
    key = os.getenv("OPENAI_API_KEY")
    if not key or not items: return None
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    text = "\n".join(f"- {i['title']} ({i['link']}): {i['summary']}" for i in items)
    body = {"model": (os.getenv("OPENAI_MODEL") or "gpt-4o-mini"), "messages": [
        {"role": "system", "content": "You write a 5-minute AI news digest. 3-6 bullet points, plain English, most useful first, each with its link. No hype."},
        {"role": "user", "content": text}]}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(),
        {"Content-Type": "application/json", "Authorization": "Bearer " + key, **UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)["choices"][0]["message"]["content"].strip()
    except Exception as e: print(f"warn: AI summary failed, sending plain list: {e}", file=sys.stderr); return None

def build(items):
    head = f"AI news digest - {datetime.now():%A %d %B %Y}\n\n"
    if not items: return head + "Nothing new in the last %d hours." % HOURS
    s = ai_summary(items)
    lst = "\n".join(f"- {i['title']}\n  {i['link']}  [{i['source']}]" for i in items)
    return head + (s + "\n\nAll links:\n" if s else "") + lst + "\n\n-- built with TaskToAgent: https://tasktoagent.com/agents/"

def send(text):
    host, to = os.getenv("SMTP_HOST"), os.getenv("EMAIL_TO")
    if not host or not to or "--dry-run" in sys.argv: print(text); return
    m = EmailMessage(); m["Subject"] = "Your AI news digest"; m["From"] = (os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER")); m["To"] = to
    m.set_content(text)
    with smtplib.SMTP(host, int((os.getenv("SMTP_PORT") or "587")), timeout=30) as s:
        s.starttls(context=ssl.create_default_context()); s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD")); s.send_message(m)
    print(f"sent digest to {to}")

if __name__ == "__main__":
    send(build(collect()))
