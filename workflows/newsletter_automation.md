# Newsletter Automation

## Objective
Given a topic, produce and send a research-backed HTML newsletter with
AI-generated infographics, via Gmail.

## One-time setup (do this before the first run)

**Perplexity API key**
1. https://www.perplexity.ai/settings/api -> create a key.
2. Paste it into `.env` as `PERPLEXITY_API_KEY`.

**Kie.ai API key**
1. https://kie.ai/api-key -> create a key.
2. Paste it into `.env` as `KIE_API_KEY`.

**Gmail OAuth (one-time browser authorization)**
1. https://console.cloud.google.com -> create/select a project.
2. Enable the "Gmail API" (APIs & Services -> Library).
3. OAuth consent screen -> External -> add your Gmail address as a test user.
4. Credentials -> Create Credentials -> OAuth client ID -> Application type
   "Desktop app".
5. Download the JSON, save it as `credentials.json` in the project root.
6. The first time `tools/send_gmail.py` runs, it opens a browser window to
   authorize; the resulting token is cached to `token.json` so later runs
   don't prompt again. If scopes ever change, delete `token.json` to
   re-authorize.

**Python environment**
```
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```
Run all tools with `./venv/Scripts/python.exe tools/<script>.py ...` (or
activate the venv first).

## Pipeline

1. **Research** — `tools/research_perplexity.py "<topic>"`
   Writes `.tmp/research/<slug>.json` with `content`, `citations`,
   `search_results`. Read this file before writing copy.

2. **Write the newsletter content** (agent does this directly — this is
   reasoning, not a deterministic step). Draft 2-4 sections from the
   research. For each section decide whether an infographic would help;
   if so, write a concrete, visual image-generation prompt for it (Nano
   Banana does well with concrete scenes/diagrams, not abstract concepts).
   Save the result as `.tmp/content/<slug>.json`:
   ```json
   {
     "title": "...",
     "subtitle": "optional dateline",
     "sections": [
       {"heading": "...", "body_html": "<p>...</p>", "image": "some-name.png"}
     ]
   }
   ```
   `image` is optional per section and must be a **filename only** (no
   path) — it must match a file that will exist in `.tmp/images/` by the
   time you format the HTML.

3. **Generate infographics** (per section that needs one) —
   `tools/generate_infographic.py "<image prompt>" --output .tmp/images/<same-filename-as-in-content-json>`
   This is an async task under the hood (create -> poll); the script
   handles polling and downloading automatically. Default timeout is 180s;
   raise `--timeout` for complex prompts if it times out.

4. **Format HTML** —
   `tools/format_newsletter_html.py --content .tmp/content/<slug>.json --output .tmp/newsletters/<slug>.html`
   Deterministic templating only — do not hand-edit the output HTML; fix
   the content JSON or the template script instead.

5. **Send** —
   `tools/send_gmail.py --to <recipient> --subject "<subject>" --html-file .tmp/newsletters/<slug>.html`
   Recipient defaults to `NEWSLETTER_RECIPIENT` in `.env` if `--to` is
   omitted. Currently that's the user's own address, for review before any
   wider send.

## Edge cases / things learned

- **Kie.ai is async.** `createTask` returns a `taskId` immediately; the
  image isn't ready until `recordInfo` reports `state: success`. States
  seen: `waiting`, `queuing`, `success`, `fail`. Don't add a `callBackUrl`
  unless you have somewhere to receive the webhook — polling is simpler
  for this use case.
- **Perplexity endpoint is `https://api.perplexity.ai/v1/sonar`**, not the
  `/router/v1/chat/completions` "Gateway" endpoint (that's a separate
  multi-model routing product, not the search-grounded Sonar API).
- **Image filenames are the link between steps.** The content JSON names
  an image by filename; the HTML embeds it as `cid:<filename>`; the send
  step attaches whatever file in `--images-dir` matches that filename.
  Keep names simple (no spaces, ASCII) and consistent across steps 2-3.
- Confirm before sending to any recipient beyond the default review
  address — this pipeline can email other people's inboxes, which isn't
  reversible.
- **Compress infographics before emailing.** Raw Nano Banana output can run
  1-2MB per image. On a slow/throttled connection that's enough to make the
  Gmail API `messages.send` write time out entirely (`TimeoutError: The
  write operation timed out` from the SSL socket, with no useful HTTP error
  to debug). `tools/generate_infographic.py` now downscales to a max width
  of 1100px and recompresses (adaptive PNG palette / quality-78 JPEG)
  before saving, which gets a typical infographic under ~350KB. If you
  still see send timeouts, check actual upload throughput first
  (`pip install` speed is a decent proxy) before assuming it's a Gmail API
  or auth problem.
- **First-run OAuth needs a test user, not just a downloaded client
  secret.** With the OAuth consent screen in "Testing" publishing status,
  Google rejects the authorization redirect for anyone not explicitly
  added under Google Cloud Console -> APIs & Services -> OAuth consent
  screen -> Audience -> Test users, even the project owner. The failure
  surfaces as a Google-hosted "Error 400" page with a request-details
  block (`redirect_uri`, `client_id`, etc.) rather than a clear "add a test
  user" message, which makes it look like a redirect URI misconfiguration.
  Add the sending Gmail address as a test user first.
