"""
Generate an image with Nano Banana (google/nano-banana) via Kie.ai.

Async task API: POST createTask -> poll recordInfo until state is a
terminal value -- confirmed against https://docs.kie.ai/market/google/nano-banana.

Usage:
    python tools/generate_infographic.py "prompt text" [--aspect-ratio 1:1] \
        [--output-format png] [--output PATH] [--poll-interval 5] [--timeout 180]

Prints the saved image path to stdout on success.
"""
import argparse
import io
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image

CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"
MODEL = "google/nano-banana"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".tmp" / "images"

TERMINAL_SUCCESS = "success"
TERMINAL_FAIL = "fail"

# Email images should stay small: this project's newsletters render at a
# 536px column width, and a slow/throttled connection (observed ~24 kB/s on
# this machine) can time out the Gmail API send if inline attachments are
# multi-megabyte. Nano Banana returns large source images, so downscale and
# recompress before saving.
MAX_IMAGE_WIDTH = 1100


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "image"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--aspect-ratio", default="1:1", help="e.g. 1:1, 16:9, 3:2 (default: 1:1)")
    parser.add_argument("--output-format", default="png", choices=["png", "jpeg"])
    parser.add_argument("--output", help="Explicit output image path (overrides default .tmp/images/<slug>.<ext>)")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Seconds between status checks")
    parser.add_argument("--timeout", type=float, default=180.0, help="Max seconds to wait for generation")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("KIE_API_KEY")
    if not api_key:
        print("ERROR: KIE_API_KEY is not set in .env", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    create_payload = {
        "model": MODEL,
        "input": {
            "prompt": args.prompt,
            "output_format": args.output_format,
            "aspect_ratio": args.aspect_ratio,
        },
    }
    resp = requests.post(CREATE_TASK_URL, headers=headers, json=create_payload, timeout=60)
    if resp.status_code != 200:
        print(f"ERROR: createTask returned {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)

    body = resp.json()
    if body.get("code") != 200:
        print(f"ERROR: createTask failed: {body}", file=sys.stderr)
        sys.exit(1)
    task_id = body["data"]["taskId"]

    deadline = time.monotonic() + args.timeout
    result_url = None
    while time.monotonic() < deadline:
        time.sleep(args.poll_interval)
        poll_resp = requests.get(
            RECORD_INFO_URL, headers=headers, params={"taskId": task_id}, timeout=60
        )
        if poll_resp.status_code != 200:
            print(f"ERROR: recordInfo returned {poll_resp.status_code}: {poll_resp.text}", file=sys.stderr)
            sys.exit(1)

        poll_body = poll_resp.json()["data"]
        state = poll_body.get("state")

        if state == TERMINAL_SUCCESS:
            import json as _json

            result_json = _json.loads(poll_body["resultJson"])
            result_url = result_json["resultUrls"][0]
            break
        if state == TERMINAL_FAIL:
            print(f"ERROR: generation failed: {poll_body.get('failCode')} {poll_body.get('failMsg')}", file=sys.stderr)
            sys.exit(1)
        # else: waiting / queuing -- keep polling

    if result_url is None:
        print(f"ERROR: timed out after {args.timeout}s waiting for taskId={task_id}", file=sys.stderr)
        sys.exit(1)

    output_path = (
        Path(args.output)
        if args.output
        else DEFAULT_OUTPUT_DIR / f"{slugify(args.prompt)}.{args.output_format}"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img_resp = requests.get(result_url, timeout=120)
    img_resp.raise_for_status()

    img = Image.open(io.BytesIO(img_resp.content))
    if img.width > MAX_IMAGE_WIDTH:
        ratio = MAX_IMAGE_WIDTH / img.width
        img = img.resize((MAX_IMAGE_WIDTH, int(img.height * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    if args.output_format == "jpeg":
        img.convert("RGB").save(buf, format="JPEG", quality=78, optimize=True)
    else:
        img.convert("P", palette=Image.ADAPTIVE, colors=64).save(buf, format="PNG", optimize=True)
    output_path.write_bytes(buf.getvalue())

    print(str(output_path))


if __name__ == "__main__":
    main()
