# Website change alert (Discord, Telegram, Slack) - free TaskToAgent agent

> **Task:** "Tell me on Discord (or Telegram, Slack or email) when a web page changes, or when a product is back in stock."

Checks the web pages you list every 15 to 60 minutes and tells you what changed: the lines of text that were added and removed. Or watch for one phrase instead, like "In stock" appearing or "Sold out" disappearing, and get one alert when it happens. Lines that only moved don't count, and you can ignore dates and counters, so you don't get spammed. Alerts go to Discord, Telegram, Slack and/or email. No browser extension, no account, no monthly fee.

Page: https://tasktoagent.com/agents/website-change-alert/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- Where to post: a Discord webhook, a Telegram bot token + chat ID (from @BotFather), a Slack incoming webhook, or an email account that can send over SMTP (any one, or several; Telegram, Slack and email are in the Python script)

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 website_change_alert.py --demo`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 website_change_alert.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python website_change_alert.py`

### Settings
| Variable | What it does |
|---|---|
| `WATCHES_FILE` | Your pages, default watches.json (copy watches.example.json): url, name, and optionally appears / disappears (a phrase), start / end (only watch the text between two phrases) and ignore (a regex for dates or counters) |
| `WATCH_URL / WATCH_APPEARS / WATCH_DISAPPEARS / WATCH_IGNORE` | Or watch a single page without a file |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook (leave every destination empty to just print) |
| `TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID` | Optional: Telegram bot token from @BotFather and the chat, group or channel ID (or @channelname) |
| `SLACK_WEBHOOK_URL` | Optional: Slack incoming webhook URL |
| `EMAIL_TO / SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD` | Optional: email the alerts |
| `FAIL_ALERT_AFTER` | Tell you once when a page can't be loaded this many checks in a row, default 3 |
| `STATE_FILE` | Default website_change_state.json (keep it between runs) |

## Run it on a schedule (every 30 minutes)
- **macOS/Linux (cron):** `crontab -e`, then add
  `*/30 * * * * cd /path/to/website-change-alert && set -a && . ./.env && set +a && /usr/bin/python3 website_change_alert.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `website_change_alert.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '*/30 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `website-change-alert.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Python, against local test pages and mock Discord, Telegram and Slack servers (Discord answered 429 first): the first run only remembered the pages; a change that was only a timestamp (ignore rule) sent nothing; a product page switching to "In stock" and a changelog gaining lines each alerted once to all three, and never again; a page that failed twice (FAIL_ALERT_AFTER=2) alerted once.
- With Slack down, Discord and Telegram still got the alert and it wasn't repeated; with every destination down, the alert was retried on the next run, exactly once. @everyone in page text never pings.
- Live pages: Hacker News front page (96 lines of text), python.org downloads (506 lines; it gzips responses, which the script handles) and a Steam store page ("Add to Cart" found). On a simulated change to the Hacker News page, 3 new lines were reported and a line that only moved was not.
- n8n workflow imported and run in a real n8n 2.43 install against local test pages and a mock Discord webhook: an "In stock" alert, a changed-lines alert (+ added, - removed) and a can't-load alert for a 404 page, each posted once. Its text extraction was also checked on the live Hacker News page (same 96 lines as the Python version).

## Honest limits
- Pages that build their content with JavaScript after loading (many big shops and dashboards) may show little or no text: the script reads the HTML the server sends, it doesn't run a browser. Check with --dry-run first.
- Some sites block automated requests or show a captcha; those pages will show up as "can't load" alerts. Be polite: every 15 to 60 minutes is plenty.
- Tested with mock Discord, Telegram and Slack servers, not real ones.
- The n8n version posts to Discord only and keeps its memory in the workflow's static data, which n8n saves only for active (not manual test) runs. Telegram, Slack and email are in the Python version.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
