# Heartbeat watchdog (dead man's switch) - free TaskToAgent agent

> **Task:** "Warn me on Discord when my nightly backup, cron job or n8n workflow silently stops running."

A self-hosted dead man's switch. Your jobs check in when they finish (touch a file, call a ping URL, or just succeed in n8n), and the watchdog alerts Discord or email once when a check-in is late and once when it's back. It catches what error alerts can't: a job that never ran because it was deactivated, the server rebooted, or cron stopped. It also catches runs that succeed but produce nothing: a backup file that is fresh but empty, or a job that checks in with ?count=0. It also does simple uptime checks on URLs.

Page: https://tasktoagent.com/agents/heartbeat-watchdog/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- A Discord webhook (or an email account that can send over SMTP)
- Optional: an n8n API key, to watch n8n workflows' last successful run

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 heartbeat_watchdog.py --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 heartbeat_watchdog.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python heartbeat_watchdog.py`

### Settings
| Variable | What it does |
|---|---|
| `CHECKS_FILE` | Your heartbeats, default checks.json (copy checks.example.json): file, ping, n8n or url, each with a max_age like 15m, 2h, 26h. Optional: min_size for files ("1MB"; the target can be a pattern like /backups/*.sql.gz, newest file counts) and min_count for pings (jobs call /ping/name?count=12, or /ping/name/fail for a failed run) |
| `DISCORD_WEBHOOK_URL` | Where alerts go |
| `EMAIL_TO / SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD` | Optional: alerts by email |
| `N8N_URL / N8N_API_KEY` | Optional: for n8n heartbeats, e.g. http://localhost:5678 |
| `PORT / PING_TOKEN` | serve mode: ping receiver port (default 8765) and an optional secret ?token= |

## Run it on a schedule (every 10 minutes (and, for ping heartbeats, keep `python3 heartbeat_watchdog.py serve` running as a service))
- **macOS/Linux (cron):** `crontab -e`, then add
  `*/10 * * * * cd /path/to/heartbeat-watchdog && set -a && . ./.env && set +a && /usr/bin/python3 heartbeat_watchdog.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `heartbeat_watchdog.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '*/10 * * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `heartbeat-watchdog.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Python, against mock Discord and n8n API servers: missing heartbeats of all four types alerted once in one message, nothing repeated while still down, one recovery message when they came back, and a second outage alerted again.
- Ping receiver: rejects a missing or wrong PING_TOKEN (403) and bad names (404), records good pings.
- 18 Oct 2026: added checks for runs that succeed but produce nothing. Tested with a mock Discord webhook: a fresh 0-byte backup next to an old 2 MB one alerted (min_size 1MB, pattern db-*.sql.gz), a ping with ?count=0 alerted (min_count 1), both in one message and not repeated; a 3 MB backup and ?count=12 sent one recovery message; /ping/name/fail alerted again; ?count=abc is refused (400); pings.json files from the earlier version still work.
- File age, n8n last successful execution (status=success, limit 1) and URL 2xx checks all tested; Discord HTTP 429 is retried; @everyone pings are disabled; --dry-run sends and saves nothing.
- n8n workflow run as an active workflow in a real n8n 2.43 install (check every minute for the test): two jobs pinged the webhook, the one with a 1-minute limit was alerted once to a mock Discord webhook, not repeated on the next check, reported back after a new ping, and alerted again when it went quiet; the job with a 60-minute limit never alerted.

## Honest limits
- A watchdog on the same server dies with it. Run it on a second machine (a Raspberry Pi or a free cloud VM) or pair it with Healthchecks.io if the whole box going down matters.
- The ping receiver has no HTTPS of its own: keep it on your LAN/VPN or behind your reverse proxy, and set PING_TOKEN.
- Tested with mock Discord and n8n API servers, not a real Discord server.
- The n8n version can't warn you when n8n itself is down; use the Python version for that.
- min_size, min_count and /fail are in the Python version; the n8n workflow only checks that a ping arrived in time.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
