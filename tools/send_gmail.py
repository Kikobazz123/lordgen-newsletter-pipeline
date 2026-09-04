"""
Send an HTML newsletter via the Gmail API, inlining any images referenced
as <img src="cid:filename.png"> by attaching matching files from --images-dir.

One-time setup (see workflows/newsletter_automation.md for full steps):
  1. Create a Google Cloud project, enable the Gmail API.
  2. Create an OAuth Client ID (Desktop app), download as credentials.json
     into the project root.
  3. First run of this script opens a browser to authorize; the resulting
     token is cached to token.json so future runs don't prompt again.

Usage:
    python tools/send_gmail.py --to someone@example.com --subject "Subject line" \
        --html-file .tmp/newsletters/topic.html [--images-dir .tmp/images]

Prints the sent message id to stdout on success.
"""
import argparse
import base64
import mimetypes
import os
import re
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"


def get_credentials() -> Credentials:
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(
                    f"ERROR: {CREDENTIALS_PATH} not found. Follow the Gmail OAuth setup "
                    "steps in workflows/newsletter_automation.md first.",
                    file=sys.stderr,
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_message(sender: str, to: str, subject: str, html_body: str, images_dir: Path) -> MIMEMultipart:
    msg = MIMEMultipart("related")
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    referenced_cids = set(re.findall(r'src="cid:([^"]+)"', html_body))
    for cid in referenced_cids:
        image_path = images_dir / cid
        if not image_path.exists():
            print(f"ERROR: html references cid:{cid} but {image_path} does not exist", file=sys.stderr)
            sys.exit(1)
        mime_type, _ = mimetypes.guess_type(str(image_path))
        subtype = mime_type.split("/")[1] if mime_type else "octet-stream"
        img = MIMEImage(image_path.read_bytes(), _subtype=subtype)
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=cid)
        msg.attach(img)

    return msg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to", help="Recipient email (default: NEWSLETTER_RECIPIENT from .env)")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--html-file", required=True)
    parser.add_argument("--images-dir", default=str(PROJECT_ROOT / ".tmp" / "images"))
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    sender = os.environ.get("GMAIL_SENDER_EMAIL")
    to = args.to or os.environ.get("NEWSLETTER_RECIPIENT")
    if not sender or not to:
        print("ERROR: GMAIL_SENDER_EMAIL and NEWSLETTER_RECIPIENT must be set in .env, or pass --to", file=sys.stderr)
        sys.exit(1)

    html_body = Path(args.html_file).read_text(encoding="utf-8")
    images_dir = Path(args.images_dir)

    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    mime_msg = build_message(sender, to, args.subject, html_body, images_dir)
    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")

    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(sent["id"])


if __name__ == "__main__":
    main()
