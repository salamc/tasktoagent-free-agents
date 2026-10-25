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
- [n8n error messages and how to fix them (index of 404 exact errors)](https://tasktoagent.com/guides/n8n-error-messages/)
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
- [n8n Supabase node errors (Invalid path specified from /rest/v1 in Host, no Route matched, table not in schema cache, RLS returning 0 items, filter parse errors)](https://tasktoagent.com/guides/n8n-supabase-node-errors/)
- [n8n Split Out, Aggregate and Summarize not working (0 items with "wasn't found in any input item", text that won't split, Aggregate dropping nulls or running twice, Multiple matches found, Summarize sum 0 on text numbers)](https://tasktoagent.com/guides/n8n-split-out-aggregate-summarize-not-working/)
- [n8n Send Email (SMTP) errors ("The connection timed out", "wrong version number", self-signed certificate, 535 Invalid login, 530 Authentication required, empty body, n8n footer, missing attachments)](https://tasktoagent.com/guides/n8n-send-email-smtp-errors/)
- [n8n HTTP Request pagination not working (endless loops with "Response Is Empty", "The returned response was identical 5x", "'null' is not a valid URL", duplicate first page, $pageCount, cursor, next URL, Link header, offset)](https://tasktoagent.com/guides/n8n-http-request-pagination-not-working/)
- [n8n Edit Fields (Set) node not working (other fields dropped, "expects a number but we got", Boolean/Array type errors, {{ }} left as text in Fixed mode, null from typos, dot notation, "The 'JSON Output' in item 0 contains invalid JSON")](https://tasktoagent.com/guides/n8n-edit-fields-set-node-not-working/): 29 real runs on n8n 2.43.7.
- [n8n Switch node not working (unmatched items dropped silently without a Fallback Output, only the first matching output used, trailing spaces vs Ignore Case, "Wrong type: is a string but was expecting a number", "The ouput 2 is not allowed", null routed as 0; 30 real runs)](https://tasktoagent.com/guides/n8n-switch-node-not-working/)
- [n8n Filter node not working (all items discarded with a green run, trailing spaces vs Case Sensitive, "Wrong type: is a string but was expecting a number", On Error: Continue hiding errors, null/empty/exists checks; 32 real runs)](https://tasktoagent.com/guides/n8n-filter-node-not-working/)
- [n8n HTML Extract not working (JavaScript-built pages return "" with a green run, only the first match without Return Array, "No property named \"data\" exists!" for binary pages, XPath "Empty sub-selector", case-sensitive classes, tables losing rows, relative links; 32 real runs)](https://tasktoagent.com/guides/n8n-html-extract-not-working/)
- [n8n Crypto node not working (HMAC of JSON.stringify(body) never matches the webhook signature, turn on Raw Body and HMAC the binary; v2 keeps the secret in a Crypto credential; secret whitespace, hex vs base64 and the sha256= prefix fail silently; Sign, Encrypt and Decrypt errors; 57 real runs)](https://tasktoagent.com/guides/n8n-crypto-node-not-working/)
- [n8n Date & Time node not working (only the new value is output until Include Input Fields; "Invalid date format" on 24/10/2026, email dates and Fixed-mode braces; 03/04 silently read as March; moment tokens give junk like YYYY-10-Oct; Format Date prints UTC, other operations use the New York default so dates land a day early; empty string gives 01/01/1970; one bad item fails all), 41 runs](https://tasktoagent.com/guides/n8n-date-time-node-not-working/)
- [n8n Sort node not sorting correctly (numeric strings sort as text, 100 before 9; dd/mm dates sorted by day; item10 before item2; one null scrambles the order; "Couldn't find the field" for wrong case, expressions or arrays; Code mode silent no-ops; Sort before Limit for top N; 33 real runs)](https://tasktoagent.com/guides/n8n-sort-node-not-working/)
- [n8n Rename Keys node not working (wrong case, a trailing space or a CSV BOM rename nothing on a green run; dots move values into or out of objects; renaming onto an existing key overwrites it; swapping two keys loses a value; regex replaces only the first match; "Invalid regular expression: ... Unterminated group"; 28 real runs on n8n 2.43.7)](https://tasktoagent.com/guides/n8n-rename-keys-not-working/)
- [n8n Respond to Webhook not working ("No Respond to Webhook node found" / "Unused Respond to Webhook node found"; only the first item returned; "Invalid JSON in 'Response Body' field" from hand-built JSON, fixed with JSON.stringify; empty 200 when no item reaches the node; errors after the response still return 200; 28 real runs)](https://tasktoagent.com/guides/n8n-respond-to-webhook-not-working/)
- [n8n GraphQL node not working ("Using variables failed" from hand-built JSON, fixed with JSON.stringify; variables silently dropped with GET or Raw format; errors on HTTP 200 fail the node and lose partial data; a 401 comes out green; "Response body is not valid JSON"; Split Out on data; 34 runs against a local mock server)](https://tasktoagent.com/guides/n8n-graphql-node-not-working/)
- [n8n Webhook file upload and binary data (the file lands under the form field name such as binary.file, not data; several files become file0, file1; octet-stream uploads get a .bin extension; raw bodies land in binary.data with a random name; base64 in JSON stays text; 422 "Failed to parse request body"; 25 real requests on n8n 2.43.7)](https://tasktoagent.com/guides/n8n-webhook-file-upload-binary-data/)
- [n8n Execution Data node not saving (keys with spaces or dashes and boolean, object or array values are dropped silently outside the editor; 10 keys max; with several items only the last value survives; keys cut to 50 and values to 512 characters; Fixed mode stores the braces; filtering by custom data needs Pro or Enterprise)](https://tasktoagent.com/guides/n8n-execution-data-not-saving/)
- [n8n Webhook authentication not working (Header Auth always 403 "Authorization data is wrong!", even when the header is missing, with an exact case-sensitive value and no query-string keys; Basic Auth 401 "Authorization is required!" / "Authentication data is wrong!"; JWT "No token provided" without the Bearer prefix, "jwt expired", "invalid signature"; 500 "No authentication data defined on node!" with no credential; secrets saved in $json.headers; 28 real requests on n8n 2.43.7)](https://tasktoagent.com/guides/n8n-webhook-authentication-not-working/)
- [n8n error workflow not triggering (an unpublished handler never runs, logged only as "is not active and cannot be executed"; no Error Trigger node; Continue On Error and successful retries skip it; CLI and manual runs don't call it; Stop and Error messages in Fixed mode keep {{ }}; execution.url points to localhost; 17 real runs on n8n 2.43.7)](https://tasktoagent.com/guides/n8n-error-workflow-not-triggering/)
- [n8n Data Table node not working ("unknown column name"; "does not match column type", "" stored as 0; date-only values stored at New York midnight; "already exists in this project" unless Reuse Existing Tables is added; like means contains; Any Condition is OR; upsert overwrites every matching row; 78 real runs)](https://tasktoagent.com/guides/n8n-data-table-not-working/)
- [n8n Remove Duplicates not working (All Fields removes nothing when one field differs; "field is missing from some input items" from a missing field, wrong case or an expression; "isn't always the same type" for 1 vs "1"; Previous Executions keeps copies inside one run or discards everything; "exceeds the maximum history size" is a hard cap; clearing history; 63 real runs)](https://tasktoagent.com/guides/n8n-remove-duplicates-not-working/)
- [n8n JWT node not working (the Payload Claims fields write expiresIn and subject, not exp and sub, so the token never expires; "Value is not a valid JWT token" from a Bearer prefix or trailing newline; "invalid algorithm" when the token alg differs from the credential, fixed with Override Algorithm; "The JWT token can't be verified" from a wrong or space-padded secret; jwt expired / jwt not active and Clock Tolerance; RS256 keys need their PEM lines; Verify puts claims under payload and never checks aud or iss; Decode checks nothing; 54 real runs)](https://tasktoagent.com/guides/n8n-jwt-node-not-working/)
- [n8n Compression node not working (one zip per item unless you Aggregate with Include Binaries and list data,data_1,data_2; duplicate file names keep one entry; unzipped files land in file_0, not data, so set Output Prefix; File extension not found, Unsupported archive format .rar/.7z, invalid zip data from an HTML page; .tar.gz named .gz is only gunzipped; 42 real runs)](https://tasktoagent.com/guides/n8n-compression-node-not-working/)
- [n8n Convert to File not working (every operation drops the other fields and outputs only the file; chained Convert gives a 4-byte BOM-only CSV; all items go into one file and File Name uses the first item; every CSV has a UTF-8 BOM; nested data becomes dot columns; big numbers become 1.23457E+19; sheet name and Text File errors; plain text or a data: URL in Move Base64 String to File gives a corrupt file on a green run; 38 real runs on n8n 2.43.7)](https://tasktoagent.com/guides/n8n-convert-to-file-not-working/)
- [n8n Markdown node not working (tables stay as raw pipes until the Tables option; single newlines merge until Simple Line Breaks; wrong field or Fixed mode gives no output on a green run; objects and numbers fail with text.replace is not a function; literal \n from AI ends up in one heading; snake_case turns into <em>; raw HTML passes through; HTML to Markdown drops data: images and adds backslash escapes), 38 runs](https://tasktoagent.com/guides/n8n-markdown-node-not-working/)
- [n8n XML node not working (binary file or wrong field gives Item has no JSON property called "data"; one element is an object, not an array, so Split Out splits junk until Explicit Array; attributes under _ and $; all values are strings; Non-whitespace before first tag, Unexpected close tag and other parse errors; JSON to XML makes one document per item), 39 runs](https://tasktoagent.com/guides/n8n-xml-node-not-working/)
- [n8n Compare Datasets not working (string vs number ids send every row to In A only / In B only with a green run, Fuzzy Compare fixes types but not case or spaces, sync fields push every match to Different until Fields to Skip Comparing, the default Different output is a diff object, duplicates leak into B only; 40 real runs)](https://tasktoagent.com/guides/n8n-compare-datasets-not-working/)
- [n8n Extract From File (CSV) not working (semicolon file read as one column, BOM "\ufeffname" first key, Latin-1 accents, "Invalid Opening Quote", "Invalid Record Length", "has no binary field 'data'", XLSX sheet and JSON array pitfalls; 32 real runs)](https://tasktoagent.com/guides/n8n-extract-from-file-csv-not-working/)
- [n8n Execute Command and Read/Write Files from Disk errors (Execute Command missing in n8n 2.x / NODES_EXCLUDE, only stderr on exit code, ~/.n8n-files is the OS HOME, 0 items on missing paths)](https://tasktoagent.com/guides/n8n-execute-command-read-write-file-errors/)
- [n8n MongoDB node errors (Authentication failed / authSource, Invalid JSON in 'Query', unknown operator $oid, Update that changes nothing)](https://tasktoagent.com/guides/n8n-mongodb-node-errors/)
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
