#!/usr/bin/env python3
"""TaskToAgent - Free game & deal alert. Python 3.9+, standard library only.
Checks Epic Games Store free games and GamerPower giveaways (no key needed), and optionally
IsThereAnyDeal for your wishlist titles hitting a price (needs a free ITAD API key).
Posts anything new to a Discord webhook, a Telegram chat (bot token + chat id) and/or a Slack incoming webhook
(or prints it). Remembers what it already sent in a state file."""
import os, sys, json, time, html, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
STATE = (os.getenv("STATE_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_games.json"))
PLATFORMS = (os.getenv("GAMERPOWER_PLATFORMS") or "pc")          # e.g. pc, steam, epic-games-store, gog
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")  # e.g. 123456789, -100123... for groups/channels, or @yourchannel
SLACK = os.getenv("SLACK_WEBHOOK_URL", "")
TG_API = (os.getenv("TELEGRAM_API") or "https://api.telegram.org")
ITAD_KEY = os.getenv("ITAD_API_KEY", "")
WATCH = [t.strip() for t in os.getenv("WATCH_GAMES", "").split(",") if t.strip()]  # titles for ITAD
MAX_PRICE = float((os.getenv("MAX_PRICE") or "10"))
COUNTRY = (os.getenv("COUNTRY") or "US")
UA = {"User-Agent": "TaskToAgent-Game-Alert/1.0 (+https://tasktoagent.com/agents/)"}

def get(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={**UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r: return json.load(r)

def epic():
    d = get(f"https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country={COUNTRY}")
    now = datetime.now(timezone.utc); out = []
    for g in d["data"]["Catalog"]["searchStore"]["elements"]:
        for block in ((g.get("promotions") or {}).get("promotionalOffers") or []):
            for o in block.get("promotionalOffers", []):
                s = datetime.fromisoformat(o["startDate"].replace("Z", "+00:00")); e = datetime.fromisoformat(o["endDate"].replace("Z", "+00:00"))
                if s <= now <= e and o.get("discountSetting", {}).get("discountPercentage") == 0:
                    slug = (g.get("productSlug") or (g.get("catalogNs", {}).get("mappings") or [{}])[0].get("pageSlug") or "")
                    out.append({"id": "epic:" + g["id"], "title": g["title"], "where": "Epic Games Store",
                                "url": f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games",
                                "note": f"FREE until {e:%d %b %H:%M} UTC"})
    return out

def gamerpower():
    d = get(f"https://www.gamerpower.com/api/giveaways?type=game&platform={urllib.parse.quote(PLATFORMS)}")
    if not isinstance(d, list): return []
    return [{"id": f"gp:{g['id']}", "title": g["title"], "where": g.get("platforms", ""), "url": g.get("open_giveaway_url") or g.get("gamerpower_url"),
             "note": f"FREE (worth {g.get('worth','?')}), ends {g.get('end_date','N/A')}"} for g in d]

def itad():
    if not ITAD_KEY or not WATCH: return []
    out = []
    for t in WATCH:
        try:
            r = get(f"https://api.isthereanydeal.com/games/lookup/v1?key={ITAD_KEY}&title={urllib.parse.quote(t)}")
            if not r.get("found"): print(f"warn: ITAD can't find {t!r}", file=sys.stderr); continue
            gid = r["game"]["id"]
            p = get(f"https://api.isthereanydeal.com/games/prices/v3?key={ITAD_KEY}&country={COUNTRY}", [gid])
            for deal in (p[0].get("deals") if p else []) or []:
                amt = deal["price"]["amount"]
                if amt <= MAX_PRICE:
                    out.append({"id": f"itad:{gid}:{deal['shop']['id']}:{amt}", "title": r["game"]["title"], "where": deal["shop"]["name"],
                                "url": deal["url"], "note": f"{amt} {deal['price']['currency']} (-{deal.get('cut',0)}%)"}); break
        except Exception as e: print(f"warn: ITAD {t}: {e}", file=sys.stderr)
    return out

def send(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {**UA, "Content-Type": "application/json"})
    for attempt in range(3):
        try: urllib.request.urlopen(req, timeout=20).read(); return
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:  # rate limited: wait as told, then retry
                try: body = json.loads(e.read() or b"{}")
                except ValueError: body = {}
                wait = body.get("retry_after") or body.get("parameters", {}).get("retry_after") or e.headers.get("Retry-After") or 2
                time.sleep(min(float(wait), 60) + 0.5); continue
            raise

def deliver(batch):
    """Post one batch everywhere configured. True if at least one destination got it."""
    ok = False
    dests = []
    if WEBHOOK:
        embeds = [{"title": i["title"][:250], "url": i["url"], "description": f"{i['note']}\n{i['where']}", "color": 0x39FF88} for i in batch]
        dests.append(("Discord", WEBHOOK, {"username": "Free Game Alert", "content": "🎮 New free games / deals", "embeds": embeds,
                                          "allowed_mentions": {"parse": []}}))
    if TG_TOKEN and TG_CHAT:
        lines = [f'🎮 <b><a href="{html.escape(i["url"], quote=True)}">{html.escape(i["title"][:200])}</a></b>\n{html.escape(i["note"])} · {html.escape(i["where"])}' for i in batch]
        dests.append(("Telegram", f"{TG_API}/bot{TG_TOKEN}/sendMessage",
                      {"chat_id": TG_CHAT, "text": "\n\n".join(lines), "parse_mode": "HTML", "disable_web_page_preview": len(batch) > 1}))
    if SLACK:
        esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines = [f"• *<{i['url']}|{esc(i['title'][:200])}>*  {esc(i['note'])} · {esc(i['where'])}" for i in batch]
        dests.append(("Slack", SLACK, {"text": ":video_game: New free games / deals\n" + "\n".join(lines)}))
    for name, url, payload in dests:
        try: send(url, payload); ok = True
        except Exception as e: print(f"warn: {name}: {e}", file=sys.stderr)
    return ok

def post(items):
    """Returns the items that were delivered (so only those get marked as seen)."""
    if not (WEBHOOK or (TG_TOKEN and TG_CHAT) or SLACK) or "--dry-run" in sys.argv:
        for i in items: print(f"[{i['where']}] {i['title']} - {i['note']}\n  {i['url']}")
        return []
    done = []
    for k in range(0, len(items), 10):  # Discord allows 10 embeds per message
        batch = items[k:k+10]
        if deliver(batch): done += batch
        time.sleep(1)
    print(f"posted {len(done)} of {len(items)} new item(s)" + ("" if len(done) == len(items) else "; the rest will be retried next run"))
    return done

def main():
    seen = set(json.load(open(STATE))) if os.path.exists(STATE) else set()
    found = []
    for src in (epic, gamerpower, itad):
        try: found += src()
        except Exception as e: print(f"warn: {src.__name__}: {e}", file=sys.stderr)
    new = [i for i in found if i["id"] not in seen]
    if not new: print("nothing new"); return
    done = post(new)
    if done: json.dump(sorted(seen | {i["id"] for i in done}), open(STATE, "w"))

if __name__ == "__main__": main()
