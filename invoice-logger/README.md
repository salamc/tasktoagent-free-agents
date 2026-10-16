# Invoice & receipt logger - free TaskToAgent agent

> **Task:** "Log every invoice and receipt I get by email into a spreadsheet: date, vendor, amount."

Finds invoice and receipt emails over IMAP, reads the email text and any text-based PDF attached, and adds one row per invoice to a CSV file (opens in Excel, Numbers or Google Sheets): date, vendor, amount, currency, invoice number. Optionally it also adds the row to a Google Sheet. Already-logged emails are skipped.

Page: https://tasktoagent.com/agents/invoice-logger/ · Made by TaskToAgent (https://tasktoagent.com) · MIT licence

## What you need
- Python 3.9+ (no extra packages) or n8n
- IMAP access to your mailbox (app password for Gmail/Outlook)
- Optional: a Google Sheet plus the included 10-line Apps Script (no Google Cloud project needed)

## 5-minute setup (Python)
1. Install Python 3.9 or newer (python.org). No `pip install` is needed: the script uses only the standard library.
2. Unzip this folder and open a terminal in it.
3. Try it without any accounts: `python3 invoice_logger.py --eml-dir sample_emails --dry-run`
4. Copy `.env.example` to `.env`, fill in your values, then load them and run for real:
   - macOS/Linux: `set -a; . ./.env; set +a; python3 invoice_logger.py`
   - Windows PowerShell: `Get-Content .env | % { if ($_ -match '^([^#=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }; python invoice_logger.py`

### Settings
| Variable | What it does |
|---|---|
| `IMAP_HOST / IMAP_USER / IMAP_PASSWORD` | Your mailbox |
| `DAYS` | How far back to look, default 30 |
| `KEYWORDS` | Subject/file words that mean 'invoice', default invoice,receipt,facture,rechnung,order confirmation... |
| `FROM_CONTAINS` | Optional: only these senders, e.g. stripe,aws,billing@ |
| `CSV_FILE` | Default ./invoices.csv |
| `SHEET_WEBHOOK_URL` | Optional: your Apps Script web app URL (see google_sheet_webhook.gs) |

## Run it on a schedule (every day at 07:00)
- **macOS/Linux (cron):** `crontab -e`, then add
  `0 7 * * * cd /path/to/invoice-logger && set -a && . ./.env && set +a && /usr/bin/python3 invoice_logger.py >> run.log 2>&1`
- **Windows:** Task Scheduler, then Create Basic Task, set the trigger, and choose Start a program `python` with argument `invoice_logger.py`, "Start in" = this folder. Set the variables with `setx NAME value` first.
- **Free cloud option:** a GitHub Actions workflow with `schedule: - cron: '0 7 * * *'` and your values as repository secrets.

## 5-minute setup (n8n, no code)
1. In n8n: **Workflows, then Import from file**, and pick `invoice-logger.n8n.json`.
2. Follow the yellow "Read me" note in the workflow (add credentials or paste your webhook).
3. Click **Test workflow**, then switch it to **Active**. The Schedule node handles timing.

## What we tested
- Ran on the included samples: a PDF invoice ($24.00, number from inside the PDF), a euro receipt with comma decimals (18,00 €) and a £1,049.99 order were parsed correctly, and a personal email was ignored.
- A second run added nothing (duplicates skipped).
- Fake IMAP test (read-only, BODY.PEEK) and the Google Sheet push tested against a mock Apps Script endpoint.
- n8n workflow imported into a real n8n install and its parsing step run on test data. The IMAP and Google Sheets nodes need your accounts, so we didn't run them.

## Honest limits
- Parsing is best effort (patterns, not AI). Check the amounts before you file taxes.
- Scanned/image PDFs have no text, so the amount stays empty; the row is still logged.
- Only simple text PDFs are read (no OCR). The n8n version reads the email text only.
- Not tested against a real mailbox or a real Google Sheet.

## Want a custom version?
Describe your task in one sentence at https://tasktoagent.com/ and we'll build and test it for you.
