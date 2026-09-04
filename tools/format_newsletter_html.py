"""
Render newsletter content (written by the agent) into email-safe HTML that
implements the LordGen AI brand guideline (see newsletter-brand-guideline.md):
dark ink field, Archivo stack, header lockup, gold issue rule, square
containers, and compliance footer.

Input is a JSON file with this shape:
{
  "title": "Newsletter title",
  "subtitle": "Optional dek shown under the title",
  "preheader": "Optional hidden preview text, 40-90 chars",
  "issue_number": "001",
  "issue_date": "3 AUGUST 2026",           # defaults to today (UTC) if omitted
  "sections": [
    {"heading": "Section heading", "body_html": "<p>...</p>", "image": "chart.png"}
  ],
  "cta": {"text": "Read the full report", "url": "https://..."},   # optional, max one
  "legal_entity": "LordGen AI",             # optional, compliance footer
  "legal_address": "...",                   # optional, compliance footer
  "reason_for_receipt": "...",              # optional, compliance footer
  "base_url": "{{BASE_URL}}",               # optional, used for /unsubscribe /archive links
  "footer_html": "Optional full override of the footer band"
}

"image" (optional per section) must be a filename that exists in --images-dir.
It is rendered as <img src="cid:<filename>"> so tools/send_gmail.py can find
the matching file in --images-dir and attach it inline with that Content-ID.
The header mark (lordgen-mark-email-96.png) is embedded the same way and
must also exist in --images-dir.

Usage:
    python tools/format_newsletter_html.py --content PATH.json --images-dir .tmp/images --output PATH.html

Prints the output path to stdout on success.
"""
import argparse
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / ".tmp" / "newsletters"
HEADER_MARK_FILENAME = "lordgen-mark-email-96.png"

FONT_STACK = "Archivo, 'Helvetica Neue', Helvetica, Arial, sans-serif"

# Brand palette (newsletter-brand-guideline.md #1)
INK = "#0A0A09"
GRAPHITE = "#141312"
GOLD = "#C9A24B"
LEAF = "#F0E2BC"
BRASS = "#8A6A24"
BONE = "#E8E6E1"
SLATE = "#8C8A85"

DEFAULT_LEGAL_ENTITY = "LordGen AI"
DEFAULT_LEGAL_ADDRESS = "[Postal address on file — update before any production send]"
DEFAULT_REASON = "You are receiving this because you subscribed to LordGen AI dispatches."
DEFAULT_BASE_URL = "{{BASE_URL}}"

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="supported-color-schemes" content="dark light">
<title>{title}</title>
<style>
  body, table, td {{ font-family: {font_stack}; }}
  .lg-body p {{ margin: 0 0 20px 0; }}
  .lg-body p:last-child {{ margin-bottom: 0; }}
  a.lg-cta {{ text-decoration: none; }}
  a.lg-unsub {{ color: {gold} !important; }}
</style>
</head>
<body style="margin:0;padding:0;background-color:{ink};">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{ink};">
{preheader}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{ink}" style="background-color:{ink};">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" bgcolor="{ink}" style="background-color:{ink};width:600px;max-width:600px;">

<!-- Header band -->
<tr><td bgcolor="{ink}" style="background-color:{ink};padding:24px 32px;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="padding-right:12px;"><img src="cid:{header_mark_cid}" width="41" height="48" alt="LordGen AI" style="display:block;color:{gold};font-family:{font_stack};font-weight:600;font-size:12px;"></td>
<td style="vertical-align:middle;">
<span style="font-family:{font_stack};font-weight:800;font-size:20px;letter-spacing:-0.7px;color:{leaf};">LORDGEN</span><span style="font-family:{font_stack};font-weight:400;font-size:14px;letter-spacing:2.3px;color:{gold};padding-left:6px;">AI</span>
</td>
</tr></table>
</td></tr>

<!-- Issue bar -->
<tr><td bgcolor="{ink}" style="background-color:{ink};padding:0 32px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="height:1px;line-height:1px;font-size:1px;background-color:{gold};">&nbsp;</td>
</tr></table>
</td></tr>
<tr><td bgcolor="{ink}" style="background-color:{ink};padding:12px 32px 0 32px;">
<span style="font-family:{font_stack};font-weight:600;font-size:11px;line-height:14px;letter-spacing:1.3px;text-transform:uppercase;color:{slate};">ISSUE {issue_number} &middot; {issue_date}</span>
</td></tr>

<!-- Title -->
<tr><td bgcolor="{ink}" style="background-color:{ink};padding:16px 32px 0 32px;">
<h1 style="margin:0;font-family:{font_stack};font-weight:800;font-size:32px;line-height:38px;letter-spacing:-1.1px;color:{leaf};">{title}</h1>
{subtitle_html}
</td></tr>

{sections_html}
{cta_html}

<!-- Footer -->
<tr><td style="padding:40px 32px 0 32px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td style="height:1px;line-height:1px;font-size:1px;background-color:{brass};">&nbsp;</td>
</tr></table>
</td></tr>
<tr><td bgcolor="{graphite}" style="background-color:{graphite};padding:24px 32px;">
{footer_html}
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

SECTION_TEMPLATE = """<tr><td bgcolor="{ink}" style="background-color:{ink};padding:{top_gap}px 32px 0 32px;">
<h2 style="margin:0 0 12px 0;font-family:{font_stack};font-weight:800;font-size:22px;line-height:28px;letter-spacing:-0.4px;color:{leaf};">{heading}</h2>
<div class="lg-body" style="font-family:{font_stack};font-weight:400;font-size:16px;line-height:26px;color:{bone};">{body_html}</div>
</td></tr>
{image_row}
"""

IMAGE_ROW_TEMPLATE = """<tr><td bgcolor="{ink}" style="background-color:{ink};padding:20px 32px 0 32px;">
<img src="cid:{cid}" alt="{alt}" width="536" style="width:100%;max-width:536px;height:auto;display:block;border-radius:0;">
</td></tr>
"""

CTA_TEMPLATE = """<tr><td bgcolor="{ink}" style="background-color:{ink};padding:40px 32px 0 32px;">
<table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td bgcolor="{gold}" style="background-color:{gold};padding:14px 28px;border-radius:0;">
<a class="lg-cta" href="{url}" style="font-family:{font_stack};font-weight:600;font-size:16px;color:{ink};text-decoration:none;">{text}</a>
</td>
</tr></table>
</td></tr>
"""

DEFAULT_FOOTER_TEMPLATE = """<div style="font-family:{font_stack};font-weight:400;font-size:12px;line-height:18px;color:{slate};">
<p style="margin:0 0 8px 0;">{reason_for_receipt}</p>
<p style="margin:0 0 8px 0;">{legal_entity} &middot; {legal_address}</p>
<p style="margin:0;"><a class="lg-unsub" href="{base_url}/unsubscribe" style="color:{gold};text-decoration:underline;">Unsubscribe</a> &nbsp;&middot;&nbsp; <a href="{base_url}/archive" style="color:{slate};text-decoration:underline;">View archive</a></p>
</div>
"""


def render_section(section: dict, images_dir: Path, top_gap: int) -> str:
    image_filename = section.get("image")
    image_row = ""
    if image_filename:
        image_path = images_dir / image_filename
        if not image_path.exists():
            print(f"ERROR: image '{image_filename}' referenced in content not found in {images_dir}", file=sys.stderr)
            sys.exit(1)
        image_row = IMAGE_ROW_TEMPLATE.format(
            ink=INK, cid=html.escape(image_filename), alt=html.escape(section.get("heading", ""))
        )

    return SECTION_TEMPLATE.format(
        ink=INK,
        leaf=LEAF,
        bone=BONE,
        font_stack=FONT_STACK,
        top_gap=top_gap,
        heading=html.escape(section["heading"]),
        body_html=section["body_html"],
        image_row=image_row,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, help="Path to content JSON file")
    parser.add_argument("--images-dir", default=str(PROJECT_ROOT / ".tmp" / "images"))
    parser.add_argument("--output", help="Output HTML path (default: .tmp/newsletters/<content-stem>.html)")
    args = parser.parse_args()

    content_path = Path(args.content)
    content = json.loads(content_path.read_text(encoding="utf-8"))
    images_dir = Path(args.images_dir)

    header_mark_path = images_dir / HEADER_MARK_FILENAME
    if not header_mark_path.exists():
        print(
            f"ERROR: header mark '{HEADER_MARK_FILENAME}' not found in {images_dir}. "
            "Copy it there from the project root before formatting.",
            file=sys.stderr,
        )
        sys.exit(1)

    subtitle_html = ""
    if content.get("subtitle"):
        subtitle_html = (
            f'<p style="margin:8px 0 0 0;font-family:{FONT_STACK};font-weight:400;'
            f'font-size:16px;line-height:24px;color:{BONE};">{html.escape(content["subtitle"])}</p>'
        )

    sections = content.get("sections", [])
    sections_html = "".join(
        render_section(s, images_dir, top_gap=40 if i > 0 else 40) for i, s in enumerate(sections)
    )

    cta = content.get("cta")
    cta_html = ""
    if cta:
        cta_html = CTA_TEMPLATE.format(
            ink=INK, gold=GOLD, font_stack=FONT_STACK,
            url=html.escape(cta["url"], quote=True), text=html.escape(cta["text"]),
        )

    footer_html = content.get("footer_html")
    if not footer_html:
        footer_html = DEFAULT_FOOTER_TEMPLATE.format(
            font_stack=FONT_STACK,
            slate=SLATE,
            gold=GOLD,
            reason_for_receipt=html.escape(content.get("reason_for_receipt", DEFAULT_REASON)),
            legal_entity=html.escape(content.get("legal_entity", DEFAULT_LEGAL_ENTITY)),
            legal_address=html.escape(content.get("legal_address", DEFAULT_LEGAL_ADDRESS)),
            base_url=content.get("base_url", DEFAULT_BASE_URL),
        )

    issue_date = content.get("issue_date") or datetime.now(timezone.utc).strftime("%-d %B %Y").upper()

    rendered = TEMPLATE.format(
        title=html.escape(content["title"]),
        preheader=html.escape(content.get("preheader", "")),
        subtitle_html=subtitle_html,
        sections_html=sections_html,
        cta_html=cta_html,
        footer_html=footer_html,
        issue_number=html.escape(str(content.get("issue_number", "001"))),
        issue_date=html.escape(issue_date),
        header_mark_cid=HEADER_MARK_FILENAME,
        font_stack=FONT_STACK,
        ink=INK,
        graphite=GRAPHITE,
        gold=GOLD,
        leaf=LEAF,
        brass=BRASS,
        bone=BONE,
        slate=SLATE,
    )

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"{content_path.stem}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    print(str(output_path))


if __name__ == "__main__":
    main()
