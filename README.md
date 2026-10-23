# Free AI agents & automations (n8n + Python)

Thirteen small, **tested** automations from [TaskToAgent](https://tasktoagent.com). Each one comes as an **n8n workflow** (import and click Active) and a **single-file Python script** (standard library only, nothing to `pip install`). Every script has a `--dry-run` mode so you can see what it does before giving it any credentials.

| Agent | What it does | Guide |
|---|---|---|
| [free-game-alert](free-game-alert/) | Posts new free games (Epic, Steam, GOG, itch.io via GamerPower) and optional price drops to Discord, Telegram or Slack | [Free Epic Games alerts in Discord](https://tasktoagent.com/guides/free-epic-games-discord-alert/) |
| [rss-to-discord](rss-to-discord/) | Posts new RSS/Atom items (YouTube, Reddit, GitHub releases…) that match your keywords to Discord, Telegram or Slack | [n8n RSS to Discord](https://tasktoagent.com/guides/n8n-rss-to-discord/) |
| [ai-news-digest](ai-news-digest/) | Emails you a morning AI-news digest, optionally summarised by any OpenAI-compatible model | [Daily AI news digest](https://tasktoagent.com/guides/ai-news-digest-email/) |
| [inbox-summariser](inbox-summariser/) | Summarises your unread email over IMAP into one short message (local-only by default) | [Daily AI email summary](https://tasktoagent.com/guides/ai-email-summary-daily/) |
| [attachment-saver](attachment-saver/) | Saves email attachments to folders, filtered by sender and file type. Never deletes mail | [Save attachments to a folder](https://tasktoagent.com/guides/save-email-attachments-to-folder/) |
| [unanswered-email-nudger](unanswered-email-nudger/) | Lists emails you sent that got no reply after N days (IMAP or Gmail). Never emails anyone | [Find unanswered emails](https://tasktoagent.com/guides/find-unanswered-emails-follow-up/) |
| [invoice-logger](invoice-logger/) | Logs invoice/receipt emails (incl. text PDFs) to CSV or Google Sheets: date, vendor, amount | [Log invoices to a spreadsheet](https://tasktoagent.com/guides/log-invoices-from-email-to-spreadsheet/) |
| [email-to-discord](email-to-discord/) | Posts new emails from one or more IMAP inboxes to Discord, Telegram or Slack, with per-inbox filters | [Forward email to Discord](https://tasktoagent.com/guides/forward-email-to-discord/) |
| [n8n-error-alert-and-backup](n8n-error-alert-and-backup/) | n8n error workflow → Discord alert, plus nightly export of all workflows to git | [n8n error workflow + backup](https://tasktoagent.com/guides/n8n-error-workflow-and-backup/) |
| [steam-wishlist-price-alert](steam-wishlist-price-alert/) | Discord, Telegram, Slack or email alert when a Steam wishlist game hits your price (Steam + CheapShark, no key) | [Steam wishlist price alerts](https://tasktoagent.com/guides/steam-wishlist-price-drop-alert-discord/) |
| [heartbeat-watchdog](heartbeat-watchdog/) | Dead man's switch: Discord/email alert when a cron job, backup or n8n workflow silently stops running | [Alert when a cron job stops running](https://tasktoagent.com/guides/alert-when-cron-job-or-n8n-workflow-stops-running/) |
| [twitch-live-alert](twitch-live-alert/) | Discord, Telegram or Slack message when your Twitch streamers go live, once per stream, no bot to host | [Twitch live notifications in Discord without a bot](https://tasktoagent.com/guides/twitch-live-notification-discord-webhook/) |
| [website-change-alert](website-change-alert/) | Discord, Telegram, Slack or email alert when a web page changes (added/removed lines) or a phrase like "In stock" appears. No browser extension | [Agent page](https://tasktoagent.com/agents/website-change-alert/) |

## Quick start
```bash
cd free-game-alert
python3 free_game_alert.py --dry-run      # no accounts needed
cp .env.example .env                       # add your Discord webhook
set -a; . ./.env; set +a; python3 free_game_alert.py
```
Scheduling (cron, Task Scheduler, GitHub Actions): https://tasktoagent.com/guides/run-python-script-on-schedule/

n8n: **Workflows → Import from file → `<agent>.n8n.json`**, then follow the yellow "Read me" note.

Each folder's README lists what we tested and the **honest limits**, meaning what we couldn't test without real credentials.

## n8n error fixes (each tested on a real n8n 2.43.7 instance)
- [n8n error messages and how to fix them (index of 197 exact errors)](https://tasktoagent.com/guides/n8n-error-messages/)
- [n8n webhook not working? Test URL vs production URL and every 404](https://tasktoagent.com/guides/n8n-webhook-not-working-404/)
- [n8n Code node: "Code doesn't return items properly" and 10 more](https://tasktoagent.com/guides/n8n-code-node-errors-return-items/)
- [n8n HTTP Request node errors: 401, 404, ECONNREFUSED, SSL](https://tasktoagent.com/guides/n8n-http-request-node-errors/)
- [n8n expression errors and empty values](https://tasktoagent.com/guides/n8n-expression-errors-undefined/)
- [n8n next node not running? Empty output and Always Output Data](https://tasktoagent.com/guides/n8n-next-node-not-running-no-output/)
- [n8n Merge node not working after an IF](https://tasktoagent.com/guides/n8n-merge-node-if-node-not-working/)
- [n8n Loop Over Items not working](https://tasktoagent.com/guides/n8n-loop-over-items-not-working/)
- [n8n Schedule Trigger not firing](https://tasktoagent.com/guides/n8n-schedule-trigger-not-working/)
- [n8n binary data not found](https://tasktoagent.com/guides/n8n-binary-data-not-found/)
- [n8n Email Trigger (IMAP) attachments: attachment_0](https://tasktoagent.com/guides/n8n-email-trigger-imap-attachments/)
- [n8n OAuth2 redirect_uri_mismatch and callback errors](https://tasktoagent.com/guides/n8n-oauth2-redirect-uri-mismatch/)
- [n8n "Credentials could not be decrypted"](https://tasktoagent.com/guides/n8n-credentials-could-not-be-decrypted/)
- [n8n "Connection lost" behind a reverse proxy](https://tasktoagent.com/guides/n8n-connection-lost-reverse-proxy/)
- [n8n won't start or you can't log in (self-hosting)](https://tasktoagent.com/guides/n8n-self-hosted-not-starting-errors/)
- [n8n broke after updating to 2.x](https://tasktoagent.com/guides/n8n-update-upgrade-errors/)
- [n8n queue mode: Redis and worker errors](https://tasktoagent.com/guides/n8n-queue-mode-redis-worker-errors/)
- [n8n 429 Too Many Requests: rate limits and retries](https://tasktoagent.com/guides/n8n-429-rate-limit-retry/)
- [n8n binary data in queue mode: worker "File not found"](https://tasktoagent.com/guides/n8n-binary-data-queue-mode/)
- [n8n Python Code node: task runner errors (venv missing, Missing auth token)](https://tasktoagent.com/guides/n8n-python-code-node-task-runner-errors/)
- [n8n Form Trigger not working (Problem loading form, Workflow could not be started)](https://tasktoagent.com/guides/n8n-form-trigger-not-working/)
- [n8n Wait node not resuming (401 Invalid token, 409 already finished, resume URL on localhost)](https://tasktoagent.com/guides/n8n-wait-node-not-resuming/)
- [n8n Postgres node errors (connection refused, password authentication failed, self-signed certificate, relation does not exist)](https://tasktoagent.com/guides/n8n-postgres-node-errors/)
- [n8n Redis node stuck or failing (WRONGPASS, NOAUTH, WRONGTYPE, self-signed certificate, Set always string)](https://tasktoagent.com/guides/n8n-redis-node-errors/)
- [n8n Postgres Trigger not firing (relation does not exist, permission denied, LISTEN channel case, stops after a restart)](https://tasktoagent.com/guides/n8n-postgres-trigger-not-working/)
- [n8n MySQL node errors (ECONNREFUSED ::1, Access denied for user, self-signed certificate, table doesn't exist)](https://tasktoagent.com/guides/n8n-mysql-node-errors/)
- [n8n Execute Workflow / sub-workflow not working](https://tasktoagent.com/guides/n8n-execute-workflow-sub-workflow-not-working/)
- [n8n timezone and date wrong (GENERIC_TIMEZONE, Luxon)](https://tasktoagent.com/guides/n8n-timezone-date-wrong/)

## More guides
- [n8n: stop posting the same item twice (Remove Duplicates across executions)](https://tasktoagent.com/guides/n8n-remove-duplicates-previous-executions/), the bug we hit in our own RSS and free-games workflows and how we fixed it
- [Post new YouTube videos to Discord automatically](https://tasktoagent.com/guides/youtube-uploads-to-discord/)
- [Discord webhooks for beginners](https://tasktoagent.com/guides/discord-webhook-beginners/)
- [How to build an AI agent without coding](https://tasktoagent.com/guides/build-ai-agent-without-coding/)
- [Hacker News daily digest by email, filtered by keywords](https://tasktoagent.com/guides/hacker-news-daily-digest-email/) (free Python script)
- [RSS to email daily digest](https://tasktoagent.com/guides/rss-to-email-daily-digest/) (free Python script)
- [Run a Python script on a schedule](https://tasktoagent.com/guides/run-python-script-on-schedule/) (cron, Task Scheduler, GitHub Actions)

## Want one for your own task?
Describe it in one sentence at **https://tasktoagent.com** and we'll build it, test it and send you the files plus a setup guide.

More: [all free agents](https://tasktoagent.com/agents/) · [guides](https://tasktoagent.com/guides/) · [@TaskToAgent on X](https://x.com/TaskToAgent) · hello@tasktoagent.com

## License
MIT. See [LICENSE](LICENSE).
