# AI news digest - free TaskToAgent agent

> **Task:** "Every morning, email me a 5-minute digest of the most useful new AI news."

Reads AI news feeds (Hacker News AI stories, Hugging Face, Simon Willison, OpenAI), keeps the last 24 hours, optionally summarises them with an AI model, and emails you the digest.

Page: https://tasktoagent.com/agents/ai-news-digest/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- An email account that can send over SMTP (Gmail with an app password works)
- Optional: an OpenAI-compatible API key for AI-written summaries (OpenAI, Groq, OpenRouter, a local Ollama server)

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 ai_news_digest.py --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 ai_news_digest.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python ai_news_digest.py`

### Settings
| Variable | What it does |
|---|---|
| `FEEDS` | Comma-separated RSS/Atom URLs (good AI defaults built in) |
| `HOURS` | How far back to look, default 24 |
| `MAX_ITEMS` | Max stories, default 12 |
| `SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD` | Your mail server, e.g. smtp.gmail.com / 587 |
| `EMAIL_TO / EMAIL_FROM` | Where to send it |
| `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL` | Optional AI summary (default gpt-4o-mini) |

## Run it on a schedule (every day at 07:00)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 7 * * * cd /path/to/ai-news-digest && set -a && . ./.env && set +a && /usr/bin/python3 ai_news_digest.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `ai_news_digest.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 7 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `ai-news-digest.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran against the four live default feeds: 12 fresh stories collected and deduplicated.
- AI-summary path tested against a mock OpenAI-compatible server.
- Email sending tested with a mocked SMTP server (message built and handed over correctly).
- n8n workflow imported and run end to end in a real n8n install (feeds live, email step mocked).

## Honest limits
- We didn't send through a real mailbox: SMTP was mocked.
- The AI summary is only as good as the model you plug in, and it costs a few cents a month on paid APIs.
- Some sites change or drop their feeds; the script skips a broken feed with a warning.
- The n8n version sends a plain list (no AI step) to keep setup to 5 minutes.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
