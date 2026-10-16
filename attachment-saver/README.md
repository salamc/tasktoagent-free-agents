# Email attachment saver - free TaskToAgent agent

> **Task:** "Save every email attachment (invoices, PDFs, screenshots) into neat folders automatically."

Scans your inbox over IMAP for emails with attachments and saves them as month/sender/filename. Filter by file type and sender, and duplicates are skipped by hash. Point it at a Google Drive, Dropbox or OneDrive synced folder and they end up in the cloud.

Page: https://tasktoagent.com/agents/attachment-saver/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or self-hosted n8n
- IMAP access to your mailbox (app password for Gmail/Outlook)
- Optional: a cloud-synced folder on your computer

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 attachment_saver.py --eml-dir sample_emails --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 attachment_saver.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python attachment_saver.py`

### Settings
| Variable | What it does |
|---|---|
| `IMAP_HOST / IMAP_USER / IMAP_PASSWORD` | Your mailbox |
| `SAVE_DIR` | Where to save, default ./saved_attachments |
| `EXTENSIONS` | Default pdf,png,jpg,jpeg,docx,xlsx,csv,zip |
| `FROM_CONTAINS` | Optional sender filter, e.g. invoice,billing@,amazon |
| `DAYS` | How far back to look, default 7 |

## Run it on a schedule (every hour)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 * * * * cd /path/to/attachment-saver && set -a && . ./.env && set +a && /usr/bin/python3 attachment_saver.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `attachment_saver.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `attachment-saver.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran on the included sample emails: PDF and PNG saved into month/sender folders, the .exe skipped, a resent duplicate invoice skipped.
- A second run saved nothing (hash index works).
- Fake IMAP test: read-only folder, BODY.PEEK fetch, sender filter.
- n8n workflow imported into a real n8n install. We didn't run it, because it needs your mailbox.

## Honest limits
- Not tested against a real mailbox (needs your login).
- It never deletes or moves emails. That's on purpose.
- The n8n version writes to disk, so it needs self-hosted n8n. n8n 2.x only writes inside ~/.n8n-files and won't create folders, so create ~/.n8n-files/attachments once (fixed 16 Oct 2026; the earlier file used a folder n8n 2.x refuses). On n8n Cloud, swap the last node for a Google Drive or Dropbox upload.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
