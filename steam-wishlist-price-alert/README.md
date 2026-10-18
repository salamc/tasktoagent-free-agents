# Steam wishlist price alert (Discord, Telegram, Slack) - free TaskToAgent agent

> **Task:** "Ping my Discord (or Telegram, or Slack) when a game on my Steam wishlist drops below my price or hits a big sale."

Reads your public Steam wishlist (or a list of games you type in), checks Steam prices and the cheapest current deal across stores via CheapShark, and alerts a Discord channel, a Telegram chat, group or channel, Slack and/or email when a game hits your target price, a big discount, or a new low since the last check. Each drop is sent once. It needs no API keys and pairs with our free game alert.

Page: https://tasktoagent.com/agents/steam-wishlist-price-alert/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- Where to post: a Discord webhook, a Telegram bot token + chat ID (from @BotFather), a Slack incoming webhook, or an email account (any one, or several; Telegram and Slack are in the Python script)
- Optional: your SteamID64, with the wishlist set to public

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 steam_wishlist_price_alert.py --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 steam_wishlist_price_alert.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python steam_wishlist_price_alert.py`

### Settings
| Variable | What it does |
|---|---|
| `STEAM_ID` | Your 17-digit SteamID64 (wishlist must be public); or use WATCH_GAMES |
| `WATCH_GAMES` | Comma-separated titles or Steam app ids, e.g. Balatro,Hades II,1030300 |
| `TARGET_PRICE` | Alert at or below this price, default 10 |
| `MIN_DISCOUNT` | ...or at least this % off, default 50 |
| `ALERT_NEW_LOW` | Alert when cheaper than last check, default 1 |
| `COUNTRY` | Steam store country, default us |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook (leave every destination empty to just print) |
| `TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID` | Optional: Telegram bot token from @BotFather and the chat, group or channel ID (or @channelname) |
| `SLACK_WEBHOOK_URL` | Optional: Slack incoming webhook URL |
| `EMAIL_TO / SMTP_HOST / SMTP_USER / SMTP_PASSWORD` | Optional: email the alerts instead or as well |

## Run it on a schedule (every 6 hours)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 */6 * * * cd /path/to/steam-wishlist-price-alert && set -a && . ./.env && set +a && /usr/bin/python3 steam_wishlist_price_alert.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `steam_wishlist_price_alert.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 */6 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `steam-wishlist-price-alert.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran against the live Steam store and CheapShark APIs: titles resolved to app ids, prices and the cheaper CheapShark deal found (Balatro 14.99 on Steam, 12.39 elsewhere).
- Read a real public Steam wishlist through Steam's public wishlist API.
- Posted to a mock Discord webhook; a second run at the same price sent nothing, and a lower price was flagged as a new low.
- n8n workflow run in a real n8n install as an active workflow: the first run posted 3 alerts to a mock Discord webhook and later runs posted nothing new.
- 18 Oct 2026: added Telegram and Slack outputs and rate-limit (429) retries. Tested with live Steam and CheapShark prices (Balatro, Hades II, Hollow Knight) against mock Discord, Telegram and Slack servers that each answered 429 first: one message to each, cheaper-elsewhere links included, nothing repeated on the next run. With Slack down, Discord and Telegram still got it and it wasn't repeated; with every destination down, nothing was marked as sent, so it retried on the next run.

## Honest limits
- Private wishlists can't be read: set Steam, then Privacy, then Game details to Public, or list the games yourself.
- CheapShark prices are in USD and cover PC key stores; Steam prices use your COUNTRY.
- Unofficial but public Steam endpoints: they can change or rate-limit.
- The n8n version checks Steam prices for the app ids you list (no wishlist import or CheapShark).
- Tested with mock Discord, Telegram and Slack servers, not real ones.
- Telegram and Slack work in the Python script; the n8n workflow posts to Discord (swap its last node for n8n's Telegram or Slack node).

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
