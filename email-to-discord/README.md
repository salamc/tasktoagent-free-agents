# Email to Discord, Telegram or Slack - free TaskToAgent agent

> **Task:** "Post new emails from my support inbox into a Discord channel or Telegram chat, with filters per inbox."

Watches one or several IMAP inboxes (Gmail, Outlook, Fastmail, any IMAP) and posts each new matching email (sender, subject, 300-character preview, attachment names) to a Discord channel, a Telegram chat, group or channel, and/or Slack. Each inbox can have its own filters and its own destinations. The first run only remembers what's already there, so nothing is flooded. Emails are never marked read.

Page: https://tasktoagent.com/agents/email-to-discord/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- IMAP access to each inbox (app password for Gmail/Outlook)
- At least one destination: a Discord webhook URL, a Telegram bot token from @BotFather plus your chat id, or a Slack incoming webhook

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 email_to_discord.py --eml-dir sample_emails --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 email_to_discord.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python email_to_discord.py`

### Settings
| Variable | What it does |
|---|---|
| `IMAP_HOST / IMAP_USER / IMAP_PASSWORD / IMAP_FOLDER` | One inbox (default folder INBOX) |
| `DISCORD_WEBHOOK_URL` | Optional: your Discord webhook |
| `TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID` | Optional: Telegram bot token from @BotFather and the chat, group or channel id (or @channelname) |
| `SLACK_WEBHOOK_URL` | Optional: Slack incoming webhook URL |
| `FROM_CONTAINS / SUBJECT_CONTAINS / EXCLUDE` | Optional comma-separated filters |
| `INBOXES_FILE` | Several inboxes: a JSON file like inboxes.example.json (own filters and destinations each) |
| `MAX_PER_RUN / PREVIEW_CHARS` | Defaults 20 / 300 |

## Run it on a schedule (every 5 minutes)
- **macOS/Linux (cron):** `crontab -e`, then add
  `*/5 * * * * cd /path/to/email-to-discord && set -a && . ./.env && set +a && /usr/bin/python3 email_to_discord.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `email_to_discord.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '*/5 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `email-to-discord.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran on the included sample emails with and without filters.
- Fake IMAP test with UIDs: the first run posted nothing, a new email was then posted once to Discord, Telegram and Slack, a filtered one skipped, and nothing was repeated on the next run.
- Posted to local stand-ins for Discord, the Telegram Bot API and Slack, including a forced rate limit (HTTP 429, then retry) on Discord and Telegram. @everyone and other pings are disabled on Discord; sender names and subjects are escaped for Telegram and Slack.
- When Slack was down, Discord and Telegram still got the email and it wasn't repeated next run; when every destination failed, the email was retried on the next run.
- n8n workflow imported into a real n8n install and its filter step run on test data. The IMAP trigger needs your mailbox, so we didn't run it.

## Honest limits
- Not tested against a real mailbox or a real Discord, Telegram or Slack workspace.
- Email content ends up in chat: don't point it at an inbox with passwords or bank codes.
- The n8n version handles one inbox per copy of the workflow and posts to Discord (swap the last node for Telegram or Slack).
- Chat shows a plain-text preview, not the full formatted email.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
