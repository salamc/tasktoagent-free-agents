# Free AI agents & automations (n8n + Python)

Five small, **tested** automations from [TaskToAgent](https://tasktoagent.com). Each one comes as an **n8n workflow** (import and click Active) and a **single-file Python script** (standard library only, nothing to `pip install`). Every script has a `--dry-run` mode so you can see what it does before giving it any credentials.

| Agent | What it does | Guide |
|---|---|---|
| [free-game-alert](free-game-alert/) | Posts new free games (Epic, Steam, GOG, itch.io via GamerPower) and optional price drops to Discord | [Free Epic Games alerts in Discord](https://tasktoagent.com/guides/free-epic-games-discord-alert/) |
| [rss-to-discord](rss-to-discord/) | Posts new RSS/Atom items (YouTube, Reddit, GitHub releases…) that match your keywords to Discord | [n8n RSS to Discord](https://tasktoagent.com/guides/n8n-rss-to-discord/) |
| [ai-news-digest](ai-news-digest/) | Emails you a morning AI-news digest, optionally summarised by any OpenAI-compatible model | [Daily AI news digest](https://tasktoagent.com/guides/ai-news-digest-email/) |
| [inbox-summariser](inbox-summariser/) | Summarises your unread email over IMAP into one short message (local-only by default) | [Daily AI email summary](https://tasktoagent.com/guides/ai-email-summary-daily/) |
| [attachment-saver](attachment-saver/) | Saves email attachments to folders, filtered by sender and file type. Never deletes mail | [Save attachments to a folder](https://tasktoagent.com/guides/save-email-attachments-to-folder/) |

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

## Want one for your own task?
Describe it in one sentence at **https://tasktoagent.com** and we'll build it, test it and send you the files plus a setup guide.

More: [all free agents](https://tasktoagent.com/agents/) · [guides](https://tasktoagent.com/guides/) · [@TaskToAgent on X](https://x.com/TaskToAgent) · hello@tasktoagent.com

## License
MIT. See [LICENSE](LICENSE).
