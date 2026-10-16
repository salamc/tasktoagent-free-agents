# n8n error alert + nightly backup - free TaskToAgent agent

> **Task:** "Tell me on Discord the moment any n8n workflow fails, and back up all my workflows to git every night."

Two safety nets for self-hosted n8n. Alerts: an error workflow posts the workflow name, failing node, error message and a link to Discord (or the Python script checks for failed executions and alerts Discord or email). Backup: every night all workflows are exported through the n8n API; the Python version commits them to a git repo and pushes it to GitHub or anywhere else.

Page: https://tasktoagent.com/agents/n8n-error-alert-and-backup/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- n8n (self-hosted for file backups; alerts work on n8n Cloud too)
- An n8n API key (Settings, then n8n API)
- A Discord webhook and/or an email account for alerts
- For git backups: Python 3.9+ and git, plus an optional private GitHub repo

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 n8n_backup_and_alert.py backup --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 n8n_backup_and_alert.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python n8n_backup_and_alert.py`

### Settings
| Variable | What it does |
|---|---|
| `N8N_URL / N8N_API_KEY` | e.g. http://localhost:5678 and your API key |
| `BACKUP_DIR` | Git folder for the backups, default ./n8n-backup (add a remote to push) |
| `DISCORD_WEBHOOK_URL` | Alerts to Discord |
| `SMTP_HOST / SMTP_USER / SMTP_PASSWORD / EMAIL_TO` | Optional: alerts by email |

## Run it on a schedule (backup every night at 02:00 (add a second line with `check` instead of `backup`, every 10 minutes, for failure alerts))
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 2 * * * cd /path/to/n8n-error-alert-and-backup && set -a && . ./.env && set +a && /usr/bin/python3 n8n_backup_and_alert.py backup >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `n8n_backup_and_alert.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 2 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `n8n-error-alert-and-backup.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Run against a real local n8n 2.43 install: a deliberately failing production workflow triggered the error workflow, which posted the workflow name, node, message and link to a mock Discord webhook.
- Nightly backup branch run inside n8n: one JSON file with all 16 workflows written, without any API keys or credential secrets.
- Python backup: 16 workflows exported, committed and pushed to a test git remote; a renamed workflow produced a one-file diff; unchanged runs make no commit.
- Python check: the first run remembers old failures; a new failure is alerted once.

## Honest limits
- The error workflow must be Active, and each workflow must pick it under Settings, then Error workflow. Manual test runs don't trigger it.
- n8n 2.x only writes files inside ~/.n8n-files, and that folder must exist. Create it once.
- Credentials (passwords, tokens) are not in the backup, so you'd re-enter them after a restore.
- Tested on a local n8n, not n8n Cloud.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
