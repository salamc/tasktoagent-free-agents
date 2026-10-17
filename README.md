# Free AI agents & automations (n8n + Python)

Ten small, **tested** automations from [TaskToAgent](https://tasktoagent.com). Each one comes as an **n8n workflow** (import and click Active) and a **single-file Python script** (standard library only, nothing to `pip install`). Every script has a `--dry-run` mode so you can see what it does before giving it any credentials.

| Agent | What it does | Guide |
|---|---|---|
| [free-game-alert](free-game-alert/) | Posts new free games (Epic, Steam, GOG, itch.io via GamerPower) and optional price drops to Discord | [Free Epic Games alerts in Discord](https://tasktoagent.com/guides/free-epic-games-discord-alert/) |
| [rss-to-discord](rss-to-discord/) | Posts new RSS/Atom items (YouTube, Reddit, GitHub releases…) that match your keywords to Discord | [n8n RSS to Discord](https://tasktoagent.com/guides/n8n-rss-to-discord/) |
| [ai-news-digest](ai-news-digest/) | Emails you a morning AI-news digest, optionally summarised by any OpenAI-compatible model | [Daily AI news digest](https://tasktoagent.com/guides/ai-news-digest-email/) |
| [inbox-summariser](inbox-summariser/) | Summarises your unread email over IMAP into one short message (local-only by default) | [Daily AI email summary](https://tasktoagent.com/guides/ai-email-summary-daily/) |
| [attachment-saver](attachment-saver/) | Saves email attachments to folders, filtered by sender and file type. Never deletes mail | [Save attachments to a folder](https://tasktoagent.com/guides/save-email-attachments-to-folder/) |
| [unanswered-email-nudger](unanswered-email-nudger/) | Lists emails you sent that got no reply after N days (IMAP or Gmail). Never emails anyone | [Find unanswered emails](https://tasktoagent.com/guides/find-unanswered-emails-follow-up/) |
| [invoice-logger](invoice-logger/) | Logs invoice/receipt emails (incl. text PDFs) to CSV or Google Sheets: date, vendor, amount | [Log invoices to a spreadsheet](https://tasktoagent.com/guides/log-invoices-from-email-to-spreadsheet/) |
| [email-to-discord](email-to-discord/) | Posts new emails from one or more IMAP inboxes to Discord, with per-inbox filters | [Forward email to Discord](https://tasktoagent.com/guides/forward-email-to-discord/) |
| [n8n-error-alert-and-backup](n8n-error-alert-and-backup/) | n8n error workflow → Discord alert, plus nightly export of all workflows to git | [n8n error workflow + backup](https://tasktoagent.com/guides/n8n-error-workflow-and-backup/) |
| [steam-wishlist-price-alert](steam-wishlist-price-alert/) | Discord/email alert when a Steam wishlist game hits your price (Steam + CheapShark, no key) | [Steam wishlist price alerts](https://tasktoagent.com/guides/steam-wishlist-price-drop-alert-discord/) |

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

## More guides
- [n8n: stop posting the same item twice (Remove Duplicates across executions)](https://tasktoagent.com/guides/n8n-remove-duplicates-previous-executions/), the bug we hit in our own RSS and free-games workflows and how we fixed it
- [Post new YouTube videos to Discord automatically](https://tasktoagent.com/guides/youtube-uploads-to-discord/)
- [Discord webhooks for beginners](https://tasktoagent.com/guides/discord-webhook-beginners/)
- [How to build an AI agent without coding](https://tasktoagent.com/guides/build-ai-agent-without-coding/)
- [Run a Python script on a schedule](https://tasktoagent.com/guides/run-python-script-on-schedule/) (cron, Task Scheduler, GitHub Actions)

## Want one for your own task?
Describe it in one sentence at **https://tasktoagent.com** and we'll build it, test it and send you the files plus a setup guide.

More: [all free agents](https://tasktoagent.com/agents/) · [guides](https://tasktoagent.com/guides/) · [@TaskToAgent on X](https://x.com/TaskToAgent) · hello@tasktoagent.com

## License
MIT. See [LICENSE](LICENSE).
