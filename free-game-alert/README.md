# Free game & deal alert - free TaskToAgent agent

> **Task:** "Ping my Discord whenever a game goes free on Epic or anywhere else, or a wishlist game drops below my price."

Checks Epic Games Store's free-games feed and GamerPower giveaways (Steam, GOG, Epic, itch and more) every few hours, and optionally IsThereAnyDeal prices for games you name. Only new finds get posted to your Discord channel.

Page: https://tasktoagent.com/agents/free-game-alert/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- A Discord server where you can create a webhook (Server settings, then Integrations, then Webhooks)
- Optional: a free IsThereAnyDeal API key for wishlist price alerts

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 free_game_alert.py --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 free_game_alert.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python free_game_alert.py`

### Settings
| Variable | What it does |
|---|---|
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL (leave empty to just print) |
| `GAMERPOWER_PLATFORMS` | pc, steam, epic-games-store, gog, itchio... default pc |
| `COUNTRY` | Store country, default US |
| `ITAD_API_KEY` | Optional IsThereAnyDeal key |
| `WATCH_GAMES` | Optional, comma-separated titles to price-watch, e.g. Hades II,Balatro |
| `MAX_PRICE` | Alert when a watched game is at or below this price, default 10 |

## Run it on a schedule (every 3 hours)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 */3 * * * cd /path/to/free-game-alert && set -a && . ./.env && set +a && /usr/bin/python3 free_game_alert.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `free_game_alert.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 */3 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `free-game-alert.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran against the live Epic and GamerPower APIs: found the current Epic freebies and a dozen GamerPower giveaways.
- Posted to a mock Discord webhook: batches of 10 embeds, correct JSON.
- Second run posted nothing (dedupe works).
- n8n workflow imported and run end to end in a real n8n install, posting 14 alerts to a mock Discord webhook.
- 16 Oct 2026 fix: the n8n file's 'Only new' step had a wrong setting and could repost old games. Fixed and re-tested as an active workflow (the second run posts nothing). Please re-download if you got it earlier.

## Honest limits
- The IsThereAnyDeal part needs your own free key, so we couldn't test it live; the code follows ITAD's documented v1/v3 endpoints.
- Epic's feed is unofficial and can change without notice.
- Doesn't read your Steam wishlist automatically; you list the titles yourself.
- We tested against a mock Discord webhook, not a real server.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
