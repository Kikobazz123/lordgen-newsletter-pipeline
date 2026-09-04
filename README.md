# LordGen Newsletter Pipeline

Research a topic, draft branded copy, generate infographics, and send a
formatted HTML newsletter over Gmail — end to end.

## Pipeline

| Stage | Tool | What it does |
|---|---|---|
| 1. Research | `tools/research_perplexity.py` | Pulls sourced research on the topic via the Perplexity Sonar API |
| 2. Visuals | `tools/generate_infographic.py` | Generates infographics via Kie.ai (nano-banana) |
| 3. Format | `tools/format_newsletter_html.py` | Renders copy into email-safe HTML (inline CSS, table layout) |
| 4. Send | `tools/send_gmail.py` | Sends through Gmail using OAuth credentials |

`workflows/newsletter_automation.md` is the orchestration brief that drives
the four stages. Brand colours, logo and wordmark live in
`newsletter-brand-guideline.md` and the `lordgen-*` asset files, so the
templates can be repointed at another brand without touching the scripts.

## Setup

```bash
python -m venv venv && venv/Scripts/activate    # Windows
pip install -r requirements.txt
cp .env.example .env                            # then fill in your keys
```

Gmail sending additionally needs a Google OAuth client. Download the client
JSON from Google Cloud Console as `credentials.json`; the first run writes
`token.json`.

## Secrets

`.env`, `credentials.json`, `token.json` and `client_secret*.json` are
gitignored and are not in this repository. Never commit them — see
`.env.example` for the variables the scripts expect.
