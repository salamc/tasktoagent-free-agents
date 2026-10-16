# RSS to Discord - free TaskToAgent agent

> **Task:** "Watch a few RSS feeds and post new items that match my keywords into a Discord channel."

Watches any RSS or Atom feeds (blogs, subreddits, YouTube channels, patch notes, Hacker News) and posts new matching items to Discord. The first run just remembers what's already there, so your channel doesn't get flooded.

Page: https://tasktoagent.com/agents/rss-to-discord/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- A Discord webhook URL

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 rss_to_discord.py --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 rss_to_discord.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python rss_to_discord.py`

### Settings
| Variable | What it does |
|---|---|
| `FEEDS` | Comma-separated feed URLs (YouTube: https://www.youtube.com/feeds/videos.xml?channel_id=...) |
| `KEYWORDS` | Comma-separated, case-insensitive; empty = everything |
| `DISCORD_WEBHOOK_URL` | Your webhook |
| `MAX_PER_RUN` | Cap per run, default 10 |

## Run it on a schedule (every 15 minutes)
- **macOS/Linux (cron):** `crontab -e`, then add
  `*/15 * * * * cd /path/to/rss-to-discord && set -a && . ./.env && set +a && /usr/bin/python3 rss_to_discord.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `rss_to_discord.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '*/15 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `rss-to-discord.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran against live Hacker News and Rock Paper Shotgun feeds with keyword filters.
- First run remembered 20 items and posted nothing; a later run posted only the new ones to a mock Discord webhook.
- Handles Discord rate limits (HTTP 429, then retry).
- n8n workflow imported and run end to end in a real n8n install (Discord mocked).

## Honest limits
- Reddit often rate-limits feed readers (HTTP 429). The script skips it and tries again next run.
- Keyword matching is plain text matching, not AI.
- n8n version: the first run posts everything currently in the feeds (our test posted 90). Run it once with the Discord node disabled first.
- Telegram or Slack instead of Discord? Swap the webhook. Ask us and we'll build it.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
