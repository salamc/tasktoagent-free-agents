#!/usr/bin/env python3
"""TaskToAgent - Steam wishlist price alert. Python 3.9+, standard library only. No API keys.
Reads your PUBLIC Steam wishlist (or a list of games you type in), checks Steam prices and the
cheapest current deal across stores via CheapShark, and alerts Discord and/or email when a game
hits your target price, a big discount, or a new low since the last check. Each drop is sent once.
Try it: python3 steam_wishlist_price_alert.py --dry-run"""
import os, sys, json, ssl, time, html, smtplib, urllib.request, urllib.parse, urllib.error
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = (os.getenv("STATE_FILE") or os.path.join(HERE, "price_state.json"))
STEAM_ID = os.getenv("STEAM_ID", "")                     # 17-digit SteamID64, wishlist must be public
GAMES = [g.strip() for g in (os.getenv("WATCH_GAMES") or "Balatro,Hades II,Hollow Knight: Silksong").split(",") if g.strip()]  # app ids or titles
CC = (os.getenv("COUNTRY") or "us")
TARGET = float((os.getenv("TARGET_PRICE") or "10"))           # alert at or below this price
MIN_DISCOUNT = int((os.getenv("MIN_DISCOUNT") or "50"))       # ...or at least this % off
ALERT_NEW_LOW = (os.getenv("ALERT_NEW_LOW") or "1") == "1"    # ...or cheaper than the last time we checked
MAX_GAMES = int((os.getenv("MAX_GAMES") or "60"))
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")   # e.g. 123456789, -100123... for groups/channels, or @yourchannel
TG_API = (os.getenv("TELEGRAM_API") or "https://api.telegram.org")
SLACK = os.getenv("SLACK_WEBHOOK_URL", "")
UA = {"User-Agent": "TaskToAgent-Steam-Price-Alert/1.0 (+https://tasktoagent.com/agents/steam-wishlist-price-alert/)"}
DRY = "--dry-run" in sys.argv

def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2: time.sleep(5 * (attempt + 1)); continue
            raise

def wishlist():
    d = get(f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?steamid={STEAM_ID}")
    items = (d.get("response") or {}).get("items") or []
    if not items: print("warn: wishlist empty or private (Steam > Profile > Privacy > Game details: Public)", file=sys.stderr)
    return [str(i["appid"]) for i in sorted(items, key=lambda i: i.get("priority", 0) or 1e9)][:MAX_GAMES]

def resolve(g):
    if g.isdigit(): return g
    r = get("https://www.cheapshark.com/api/1.0/games?" + urllib.parse.urlencode({"title": g, "limit": 5}))
    hit = next((x for x in r if x.get("steamAppID") and x["external"].lower() == g.lower()), None) or next((x for x in r if x.get("steamAppID")), None)
    if not hit: print(f"warn: no Steam game found for {g!r}", file=sys.stderr); return None
    return hit["steamAppID"]

def steam_prices(ids):
    out = {}
    for k in range(0, len(ids), 50):  # price_overview filter accepts many app ids at once
        d = get(f"https://store.steampowered.com/api/appdetails?appids={','.join(ids[k:k+50])}&cc={CC}&filters=price_overview")
        for aid, v in d.items():
            p = (v.get("data") or {}).get("price_overview") if v.get("success") and isinstance(v.get("data"), dict) else None
            if p: out[aid] = {"price": p["final"] / 100, "was": p["initial"] / 100, "cut": p["discount_percent"], "cur": p["currency"]}
    return out

def names(ids):
    out = {}
    for aid in ids:
        try:
            r = get(f"https://www.cheapshark.com/api/1.0/games?steamAppID={aid}")
            if r: out[aid] = {"name": r[0]["external"], "cheapest": float(r[0]["cheapest"]), "deal": r[0]["cheapestDealID"]}
        except Exception as e: print(f"warn: CheapShark {aid}: {e}", file=sys.stderr)
        time.sleep(0.4)  # be nice to the free API
    return out

def send(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {**UA, "Content-Type": "application/json"})
    for attempt in range(3):
        try: urllib.request.urlopen(req, timeout=20).read(); return
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:  # rate limited: wait as told, then retry
                try: body = json.loads(e.read() or b"{}")
                except ValueError: body = {}
                wait = body.get("retry_after") or (body.get("parameters") or {}).get("retry_after") or e.headers.get("Retry-After") or 2
                time.sleep(min(float(wait), 60) + 0.5); continue
            raise

def describe(h):
    """(price text, cheaper-elsewhere text or '', store url)"""
    price = f"{h['price']:.2f} {h['cur']} on Steam" + (f" (-{h['cut']}%, was {h['was']:.2f})" if h['cut'] else "")
    cheaper = (f"cheapest anywhere {h['cheapest']:.2f} USD", f"https://www.cheapshark.com/redirect?dealID={h['deal']}") \
        if h.get("cheapest") is not None and h.get("deal") and h["cheapest"] < h["price"] else None
    return price, cheaper, f"https://store.steampowered.com/app/{h['id']}/"

def notify(hits):
    """Send everywhere configured. True if at least one destination got it, False if all failed, None if only printed."""
    plain = []
    for h in hits:
        price, cheaper, url = describe(h)
        plain.append(f"{h['name']}: {price}" + (f" · {cheaper[0]} {cheaper[1]}" if cheaper else "") + f"\n   {h['why']} · {url}")
    text = "Price drop on your wishlist\n" + "\n".join(plain)
    tg = TG_TOKEN and TG_CHAT
    if DRY or not (WEBHOOK or tg or SLACK or os.getenv("EMAIL_TO")): print(text); return None
    ok = False
    def attempt(name, fn):
        nonlocal ok
        try: fn(); ok = True
        except Exception as e: print(f"warn: {name}: {e}", file=sys.stderr)
    for k in range(0, len(hits), 8):
        batch = hits[k:k+8]
        if WEBHOOK:
            lines = []
            for h in batch:
                price, cheaper, url = describe(h)
                lines.append(f"🎮 **{h['name']}**: {price}" + (f" · {cheaper[0]} <{cheaper[1]}>" if cheaper else "") + f"\n   {h['why']} · <{url}>")
            attempt("Discord", lambda: send(WEBHOOK, {"username": "Wishlist Price Alert", "content": "\n".join(lines)[:1990], "allowed_mentions": {"parse": []}}))
        if tg:
            lines = []
            for h in batch:
                price, cheaper, url = describe(h)
                lines.append(f'💸 <b><a href="{html.escape(url, quote=True)}">{html.escape(h["name"][:200])}</a></b>: {html.escape(price)}'
                             + (f' · <a href="{html.escape(cheaper[1], quote=True)}">{html.escape(cheaper[0])}</a>' if cheaper else "") + f"\n{html.escape(h['why'])}")
            attempt("Telegram", lambda: send(f"{TG_API}/bot{TG_TOKEN}/sendMessage", {"chat_id": TG_CHAT, "text": "Price drop on your wishlist\n\n" + "\n\n".join(lines),
                                                                                  "parse_mode": "HTML", "disable_web_page_preview": len(batch) > 1}))
        if SLACK:
            esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines = []
            for h in batch:
                price, cheaper, url = describe(h)
                lines.append(f"• *<{url}|{esc(h['name'][:200])}>*: {esc(price)}" + (f" · <{cheaper[1]}|{esc(cheaper[0])}>" if cheaper else "") + f"  _{esc(h['why'])}_")
            attempt("Slack", lambda: send(SLACK, {"text": ":money_with_wings: Price drop on your wishlist\n" + "\n".join(lines)}))
        if k + 8 < len(hits): time.sleep(1)
    if os.getenv("EMAIL_TO"):
        def mail():
            m = EmailMessage(); m["Subject"] = f"{len(hits)} wishlist price drop(s)"; m["To"] = os.environ["EMAIL_TO"]
            m["From"] = (os.getenv("EMAIL_FROM") or (os.getenv("SMTP_USER") or os.environ["EMAIL_TO"])); m.set_content(text)
            with smtplib.SMTP((os.getenv("SMTP_HOST") or "smtp.gmail.com"), int((os.getenv("SMTP_PORT") or "587"))) as s:
                s.starttls(context=ssl.create_default_context()); s.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")); s.send_message(m)
        attempt("email", mail)
    print(f"alerted {len(hits)} price drop(s)" if ok else "every destination failed; will retry next run")
    return ok

def main():
    ids = list(dict.fromkeys(wishlist() if STEAM_ID else [i for i in (resolve(g) for g in GAMES) if i]))
    if not ids: print("nothing to watch"); return
    prices, meta = steam_prices(ids), names(ids)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    hits = []
    for aid in ids:
        p = prices.get(aid)
        if not p: continue  # free, unreleased or not sold in your country
        prev = state.get(aid, {}).get("price")
        why = [w for w, ok in ((f"at or below your {TARGET:.2f} target", p["price"] <= TARGET), (f"{p['cut']}% off", p["cut"] >= MIN_DISCOUNT),
                               (f"new low since last check (was {prev})", ALERT_NEW_LOW and prev is not None and p["price"] < prev)) if ok]
        already = state.get(aid, {}).get("alerted") == p["price"]
        if why and not already: hits.append({"id": aid, "name": meta.get(aid, {}).get("name", f"App {aid}"), **p, **{k: meta.get(aid, {}).get(k) for k in ("cheapest", "deal")}, "why": ", ".join(why)})
        old = state.get(aid, {})
        state[aid] = {"price": p["price"], "alerted": p["price"] if why else None, "_old": old}
    if hits and notify(hits) is False:
        for h in hits: state[h["id"]] = state[h["id"]]["_old"]  # nothing delivered: keep the old state so it is retried
    for v in state.values(): v.pop("_old", None)
    if not hits: print(f"checked {len(ids)} game(s): no new price drops")
    if not DRY: json.dump(state, open(STATE, "w"), indent=1)

if __name__ == "__main__": main()
