#!/usr/bin/env python3
"""TaskToAgent - Free game & deal alert. Python 3.9+, standard library only.
Checks Epic Games Store free games and GamerPower giveaways (no key needed), and optionally
IsThereAnyDeal for your wishlist titles hitting a price (needs a free ITAD API key).
Posts anything new to a Discord webhook (or prints it). Remembers what it already sent in a state file."""
import os, sys, json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
STATE = (os.getenv("STATE_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_games.json"))
PLATFORMS = (os.getenv("GAMERPOWER_PLATFORMS") or "pc")          # e.g. pc, steam, epic-games-store, gog
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

def post(items):
    if not WEBHOOK or "--dry-run" in sys.argv:
        for i in items: print(f"[{i['where']}] {i['title']} - {i['note']}\n  {i['url']}")
        return
    for k in range(0, len(items), 10):  # Discord allows 10 embeds per message
        embeds = [{"title": i["title"][:250], "url": i["url"], "description": f"{i['note']}\n{i['where']}", "color": 0x39FF88} for i in items[k:k+10]]
        req = urllib.request.Request(WEBHOOK, json.dumps({"username": "Free Game Alert", "content": "🎮 New free games / deals", "embeds": embeds}).encode(),
                                     {**UA, "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20).read(); time.sleep(1)
    print(f"posted {len(items)} item(s) to Discord")

def main():
    seen = set(json.load(open(STATE))) if os.path.exists(STATE) else set()
    found = []
    for src in (epic, gamerpower, itad):
        try: found += src()
        except Exception as e: print(f"warn: {src.__name__}: {e}", file=sys.stderr)
    new = [i for i in found if i["id"] not in seen]
    if not new: print("nothing new"); return
    post(new)
    if "--dry-run" not in sys.argv: json.dump(sorted(seen | {i["id"] for i in new}), open(STATE, "w"))

if __name__ == "__main__": main()
