# Unanswered email nudger - free TaskToAgent agent

> **Task:** "Every weekday morning, show me the emails I sent that still have no reply after 3 days."

Reads your Sent folder and inbox over IMAP (read-only, headers only) and lists every email you sent 3+ days ago where nobody has replied in the thread yet: quotes, invoices, bookings, intros. It prints the list or emails it to you. It never sends anything to the people you wrote to.

Page: https://tasktoagent.com/agents/unanswered-email-nudger/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages), or n8n with a Gmail credential
- IMAP access to your mailbox (Gmail/Outlook: turn on 2-step verification and create an app password)

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 unanswered_email_nudger.py --eml-dir sample_emails --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 unanswered_email_nudger.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python unanswered_email_nudger.py`

### Settings
| Variable | What it does |
|---|---|
| `IMAP_HOST / IMAP_USER / IMAP_PASSWORD` | e.g. imap.gmail.com / you@gmail.com / your app password |
| `DAYS` | No reply after this many days, default 3 |
| `LOOKBACK_DAYS` | Ignore sent mail older than this, default 21 |
| `SENT_FOLDER` | Auto-detected (e.g. [Gmail]/Sent Mail); set it if detection fails |
| `REPLY_FOLDERS` | Where replies land, default INBOX (Gmail: add [Gmail]/All Mail if you archive) |
| `MY_ADDRESSES` | Your addresses/aliases, comma-separated (default IMAP_USER) |
| `SMTP_HOST / SMTP_PORT / EMAIL_TO` | Optional: email the list to yourself (reuses your IMAP login) |

## Run it on a schedule (every weekday at 08:00)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 8 * * 1-5 cd /path/to/unanswered-email-nudger && set -a && . ./.env && set +a && /usr/bin/python3 unanswered_email_nudger.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `unanswered_email_nudger.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 8 * * 1-5'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `unanswered-email-nudger.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran on the included sample sent/inbox emails: only the quote with no reply is listed; replies matched by In-Reply-To and by sender + subject; noreply recipients and recent emails skipped.
- Fake IMAP server test: Sent folder auto-detected from the \Sent flag, folders opened read-only, only headers fetched with BODY.PEEK (nothing marked read).
- Report email tested with a mocked SMTP server: it goes to you only, never to the people you emailed.
- n8n (Gmail) workflow imported into a real n8n install and its matching logic run on test data. We didn't run the Gmail nodes, because they need your Gmail login.

## Honest limits
- Not tested against a real mailbox (needs your login).
- A reply that lands in a folder it doesn't read (e.g. archived in Gmail) isn't seen: add that folder to REPLY_FOLDERS.
- Replies from a different address than the one you wrote to, with a changed subject, can be missed.
- It only lists; it never writes follow-ups. That's on purpose.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
