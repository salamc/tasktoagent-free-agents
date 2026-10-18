# Inbox summariser - free TaskToAgent agent

> **Task:** "Every morning, summarise my unread emails and tell me which ones need a reply."

Reads your unread emails from the last 24 hours over IMAP (Gmail, Outlook, Fastmail, iCloud...) without marking them as read, splits people from newsletters, groups replies into conversations, puts the emails that look like they need a reply first, optionally asks an AI for a short summary, and emails or prints it.

Page: https://tasktoagent.com/agents/inbox-summariser/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages), or n8n with a Gmail credential
- IMAP access to your mailbox (Gmail/Outlook: turn on 2-step verification and create an app password)
- Optional: an OpenAI-compatible API key for 'needs a reply' detection

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 inbox_summariser.py --eml-dir sample_emails --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 inbox_summariser.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python inbox_summariser.py`

### Settings
| Variable | What it does |
|---|---|
| `IMAP_HOST / IMAP_USER / IMAP_PASSWORD` | e.g. imap.gmail.com / you@gmail.com / your app password |
| `IMAP_FOLDER` | Default INBOX |
| `HOURS` | Default 24 |
| `PEOPLE` | Optional: comma-separated addresses or @domains always treated as people, e.g. @myclient.com |
| `BULK` | Optional: addresses or @domains always treated as newsletters |
| `SMTP_HOST, EMAIL_TO` | Optional: email the summary (reuses your IMAP login by default) |
| `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL` | Optional AI summary (only emails from people are sent, newsletters are just counted) |

## Run it on a schedule (every day at 08:00)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 8 * * * cd /path/to/inbox-summariser && set -a && . ./.env && set +a && /usr/bin/python3 inbox_summariser.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `inbox_summariser.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 8 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `inbox-summariser.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran on the included sample emails: people and newsletters split correctly, HTML emails converted to text.
- Ran through a fake IMAP server: confirmed the folder is opened read-only and emails are fetched with BODY.PEEK (never marked read).
- AI and SMTP paths tested with mocks.
- n8n (Gmail) workflow imported into a real n8n install. We didn't run it, because it needs your Gmail login.
- 18 Oct 2026 update (asked for on Reddit): replies are grouped into one conversation (References/In-Reply-To, or the same subject without Re:/Fwd:), emails that ask something come first, newsletters are counted per sender, and you can pin senders with PEOPLE / BULK. Tested on 8 sample emails through a fake IMAP server and mock AI/SMTP: a 2-message thread shown once, 4 newsletters detected (List-Unsubscribe, List-Id, Precedence: bulk, Auto-Submitted), the AI request contained no newsletter text, AI failure fell back to the plain summary, no flags changed.
- n8n summary step tested with Gmail-shaped data: grouped by Gmail threadId, Gmail Updates/Social/Forums tabs counted as notifications.

## Honest limits
- We didn't connect to a real mailbox; that needs your login.
- Your email text goes to the AI provider if you set an API key. Leave it unset to keep everything local.
- Newsletter detection and 'may need a reply' are simple rules (mailing-list headers, no-reply senders; question marks and phrases like 'can you' or 'by Friday'), not AI. Use PEOPLE / BULK to fix a sender, or add an API key for an AI summary.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
