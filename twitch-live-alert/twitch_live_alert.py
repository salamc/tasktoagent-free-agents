#!/usr/bin/env python3
"""TaskToAgent - Twitch live alert. Python 3.9+, standard library only.
Asks Twitch's official API which of your channels are live and posts one message per new stream
to Discord (webhook), Telegram and/or Slack. No bot to host: run it every few minutes with cron.
  python3 twitch_live_alert.py --demo      # no accounts needed: shows what the alerts look like
  python3 twitch_live_alert.py --dry-run   # real Twitch data, prints instead of posting, saves nothing
Page: https://tasktoagent.com/agents/twitch-live-alert/ · MIT licence"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

ID_URL = (os.getenv("TWITCH_ID_URL") or "https://id.twitch.tv/oauth2/token")
API_URL = (os.getenv("TWITCH_API_URL") or "https://api.twitch.tv/helix/streams")
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
CHANNELS = list(dict.fromkeys(c.strip().lower().lstrip("@").split("/")[-1] for c in os.getenv("CHANNELS", "").split(",") if c.strip()))
GAMES = [g.strip().lower() for g in os.getenv("GAMES", "").split(",") if g.strip()]
DISCORD = os.getenv("DISCORD_WEBHOOK_URL", "")
ROLE = os.getenv("DISCORD_ROLE_ID", "").strip()
TG_TOKEN, TG_CHAT = os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", "")
TG_API = (os.getenv("TELEGRAM_API_URL") or "https://api.telegram.org")
SLACK = os.getenv("SLACK_WEBHOOK_URL", "")
STATE = (os.getenv("STATE_FILE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "twitch_live_state.json"))
DEMO, DRY = "--demo" in sys.argv, "--dry-run" in sys.argv
UA = "TaskToAgent-Twitch-Live-Alert/1.0 (+https://tasktoagent.com/agents/twitch-live-alert/)"

def call(url, data=None, headers=None, form=False, tries=3):
    body = None
    if data is not None:
        body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
    h = {"User-Agent": UA, **({"Content-Type": "application/x-www-form-urlencoded" if form else "application/json"} if body else {}), **(headers or {})}
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h), timeout=25) as r:
                raw = r.read()
                try: return json.loads(raw) if raw.strip() else {}
                except ValueError: return {"text": raw.decode("utf-8", "replace")}  # e.g. Slack answers "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                try:
                    j = json.loads(e.read() or b"{}")  # Discord: retry_after, Telegram: parameters.retry_after
                    wait = float(j.get("retry_after") or (j.get("parameters") or {}).get("retry_after") or e.headers.get("Retry-After") or 2)
                except Exception: wait = 2
                time.sleep(min(wait, 30)); continue
            raise

def load_state():
    try: return json.load(open(STATE))
    except (OSError, ValueError): return {}

def token(state, fresh=False):
    if not fresh and state.get("token") and state.get("token_exp", 0) > time.time() + 300: return state["token"]
    t = call(ID_URL, {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"}, form=True)
    state["token"], state["token_exp"] = t["access_token"], time.time() + int(t.get("expires_in", 3600))
    return state["token"]

def live_streams(state):
    out = []
    for i in range(0, len(CHANNELS), 100):  # Helix takes up to 100 user_login per request
        q = urllib.parse.urlencode([("user_login", c) for c in CHANNELS[i:i + 100]] + [("first", "100")])
        for attempt in (0, 1):
            try:
                out += call(f"{API_URL}?{q}", headers={"Client-Id": CLIENT_ID, "Authorization": f"Bearer {token(state, fresh=attempt == 1)}"})["data"]; break
            except urllib.error.HTTPError as e:
                if e.code != 401 or attempt: raise  # 401: token expired or revoked, get a new one once
    return [s for s in out if s.get("type", "live") == "live"]

def message(s):
    return (f"🔴 {s['user_name']} is live: {s['title'] or '(no title)'}\n"
            f"Playing {s.get('game_name') or 'something'} · https://twitch.tv/{s['user_login']}")

def send(s):
    """Post to every configured place. A place that fails is reported but doesn't block the others."""
    text, ok, errors = message(s), 0, []
    targets = []
    if DISCORD:
        bold = text.replace(s["user_name"], f"**{s['user_name']}**", 1)
        targets.append(("Discord", DISCORD, {"username": "Twitch Live Alert", "content": (f"<@&{ROLE}> " if ROLE else "") + bold,
                                             "allowed_mentions": {"parse": [], "roles": [ROLE] if ROLE else []}}))
    if TG_TOKEN and TG_CHAT:
        targets.append(("Telegram", f"{TG_API}/bot{TG_TOKEN}/sendMessage", {"chat_id": TG_CHAT, "text": text}))
    if SLACK:
        targets.append(("Slack", SLACK, {"text": text}))
    for name, url, payload in targets:
        try: call(url, payload); ok += 1
        except Exception as e: errors.append(name); print(f"warn: {name} post failed for {s['user_login']}: {e}", file=sys.stderr)
    if not ok: raise RuntimeError(f"every post failed ({', '.join(errors)}); will retry next run")

DEMO_DATA = [{"id": "40001", "user_login": "your_friend", "user_name": "Your_Friend", "title": "Ranked grind, come say hi", "game_name": "Valorant", "type": "live"},
             {"id": "40002", "user_login": "speedrunner", "user_name": "SpeedRunner", "title": "Any% world record attempts @everyone", "game_name": "Celeste", "type": "live"}]

def main():
    if not DEMO:
        missing = [k for k, v in (("TWITCH_CLIENT_ID", CLIENT_ID), ("TWITCH_CLIENT_SECRET", CLIENT_SECRET), ("CHANNELS", CHANNELS)) if not v]
        if missing: sys.exit(f"Missing {', '.join(missing)}. Try `python3 {os.path.basename(__file__)} --demo` first, then fill in .env (see README).")
    state = load_state()
    streams = DEMO_DATA if DEMO else live_streams(state)
    seen = state.get("live", {})
    new = [s for s in streams if seen.get(s["user_login"]) != s["id"]]
    if GAMES: new = [s for s in new if (s.get("game_name") or "").lower() in GAMES]
    posting = not (DEMO or DRY) and (DISCORD or (TG_TOKEN and TG_CHAT) or SLACK)
    # Streams still live from last run, or skipped by GAMES, count as done
    done = {s["user_login"]: s["id"] for s in streams if s not in new}
    try:
        for s in new:
            if posting: send(s); time.sleep(0.5)
            else: print(message(s) + "\n")
            done[s["user_login"]] = s["id"]
    finally:  # save even if a post failed, so what did go out isn't repeated next run
        if not (DEMO or DRY):
            state["live"] = done
            json.dump(state, open(STATE, "w"))
    print(f"{len(streams)} live, {len(new)} new" + ("" if posting else " (printed, nothing posted)"), file=sys.stderr)

if __name__ == "__main__":
    main()
