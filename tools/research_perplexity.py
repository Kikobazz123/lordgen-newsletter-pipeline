"""
Research a topic using Perplexity's Sonar API (web-grounded, with citations).

Usage:
    python tools/research_perplexity.py "topic or question" [--model sonar-pro] [--output PATH]

Writes a JSON file to .tmp/research/<slug>.json containing:
    { "topic": str, "model": str, "content": str, "citations": [str], "search_results": [...] }

Prints the output path to stdout on success.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

API_URL = "https://api.perplexity.ai/v1/sonar"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".tmp" / "research"

SYSTEM_PROMPT = (
    "You are a research assistant preparing source material for a newsletter. "
    "Provide accurate, well-organized research on the given topic: key facts, "
    "recent developments (prioritize the last few months), relevant statistics, "
    "and notable expert perspectives. Be specific and concrete rather than generic. "
    "Do not write the newsletter itself -- just the researched material."
)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "topic"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", help="Topic or question to research")
    parser.add_argument(
        "--model",
        default="sonar-pro",
        choices=["sonar", "sonar-pro", "sonar-reasoning-pro", "sonar-deep-research"],
        help="Perplexity model to use (default: sonar-pro)",
    )
    parser.add_argument("--output", help="Explicit output JSON path (overrides default .tmp/research/<slug>.json)")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        print("ERROR: PERPLEXITY_API_KEY is not set in .env", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": args.topic},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        print(f"ERROR: Perplexity API returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    message = data["choices"][0]["message"]["content"]
    citations = data.get("citations", [])
    search_results = data.get("search_results", [])

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"{slugify(args.topic)}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "topic": args.topic,
                "model": args.model,
                "content": message,
                "citations": citations,
                "search_results": search_results,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(str(output_path))


if __name__ == "__main__":
    main()
