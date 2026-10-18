# Twitch live alert - free TaskToAgent agent

> **Task:** "Post in my Discord server when my favourite Twitch streamers go live."

Asks Twitch's official API which of your channels are live and posts one message per new stream to a Discord channel webhook, a Telegram chat or Slack. No bot to invite or host: it runs every few minutes from cron or n8n and remembers each stream id, so a stream is announced once. Optional role ping and game filter.

Page: https://tasktoagent.com/agents/twitch-live-alert/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- A free Twitch app (Client ID and Client Secret from dev.twitch.tv/console)
- A Discord webhook, a Telegram bot token and chat id, or a Slack incoming webhook

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 twitch_live_alert.py --demo`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 twitch_live_alert.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python twitch_live_alert.py`

### Settings
| Variable | What it does |
|---|---|
| `TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET` | From your app at dev.twitch.tv/console |
| `CHANNELS` | Comma-separated channel names (twitch.tv/name), any number |
| `DISCORD_WEBHOOK_URL` | Where alerts go (channel settings, then Integrations, then Webhooks) |
| `DISCORD_ROLE_ID` | Optional: ping only this role; @everyone in stream titles never pings |
| `GAMES` | Optional: only announce streams in these games, e.g. Valorant,Minecraft |
| `TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID` | Optional: also post to Telegram |
| `SLACK_WEBHOOK_URL` | Optional: also post to Slack |
| `STATE_FILE` | Default twitch_live_state.json (keep it between runs) |

## Run it on a schedule (every 3 minutes)
- **macOS/Linux (cron):** `crontab -e`, then add
  `*/3 * * * * cd /path/to/twitch-live-alert && set -a && . ./.env && set +a && /usr/bin/python3 twitch_live_alert.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `twitch_live_alert.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '*/3 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `twitch-live-alert.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Python, against local stand-ins for the Twitch token and Helix streams APIs, Discord, Telegram and Slack: a channel going live was posted once to all three, the same stream was never posted again, a second channel going live posted only that one, going offline cleared it, and a new stream from the same channel was announced again.
- The Twitch app token is cached in the state file and reused; when Helix answered 401 the script fetched a new token once and carried on. Discord and Telegram HTTP 429 replies were waited out and retried.
- A stream title containing @everyone was posted as plain text with mentions disabled; DISCORD_ROLE_ID pings only that role. GAMES=Valorant skipped a Minecraft stream. If Slack was down, Discord and Telegram still posted and the stream wasn't repeated next run; if every destination failed, it was retried on the next run.
- --demo shows sample alerts with no accounts; --dry-run uses real Twitch data and posts and saves nothing.
- n8n workflow run as an active workflow in a real n8n 2.43 install (every minute for the test, mock Twitch and Discord): the first run posted the live channel, the second posted nothing, and when a second channel went live only that one was posted.

## Honest limits
- Not tested with real Twitch keys or a real Discord server: Twitch and Discord were local stand-ins that follow their documented APIs. The real Helix endpoint does answer 401 without a token, as the script expects.
- A check every 3 minutes means an alert can arrive up to 3 minutes after the stream starts. Twitch's EventSub is instant but needs a public HTTPS server.
- If a streamer's connection drops and Twitch starts a new stream, it gets a new id and is announced again.
- The n8n version posts to Discord only and gets a fresh token each run; role pings, game filter, Telegram and Slack are in the Python version.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
