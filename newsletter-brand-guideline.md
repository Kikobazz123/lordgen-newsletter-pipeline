# LordGen AI — Newsletter Brand Guideline

**Scope:** the newsletter demo only. Everything here derives from *Identity Standard · Vol. 01*. Where the Standard was silent, a value is marked **[new]** — those are the decisions you should ratify or overrule before the consultancy work starts.

---

## 1. Colour

| Role | Name | Hex | Use |
|---|---|---|---|
| Field | Ink | `#0A0A09` | Every background. Carries ~80% of the surface. |
| Raised field | Graphite | `#141312` | Cards, quote blocks, the footer band. |
| Primary | Regal Gold | `#C9A24B` **[new]** | Rules, eyebrows, links, the mark. Under 15% of any surface. |
| Trim | Leaf | `#F0E2BC` | Headlines, the centre member of the mark. |
| Trim | Brass | `#8A6A24` | Borders and dividers only. |
| Body text | Bone | `#E8E6E1` **[new]** | Paragraph copy on ink. |
| Muted | Slate | `#8C8A85` **[new]** | Captions, dates, legal, unsubscribe. |

The Standard labels Regal Gold as primary but prints no hex — `#C9A24B` is sampled off the sheet. Lock it, because every asset from here depends on it.

**Contrast on ink (WCAG):** Bone 15.9:1 · Leaf 15.4:1 · Gold 8.3:1 · Slate 5.7:1 · Brass 3.9:1. Brass fails body-text contrast — keep it to rules and borders, never words.

Standing rule from the Standard, restated because email tempts you to break it: **gold is never a background for body copy.** Gold panels hold ink text only.

## 2. Type

Archivo does not render in Outlook or most desktop clients. Always ship the full stack:

```
font-family: Archivo, 'Helvetica Neue', Helvetica, Arial, sans-serif;
```

| Role | Weight | Size / line-height | Tracking |
|---|---|---|---|
| Issue title | 800 | 32 / 38 px | −3.5% |
| Section head | 800 | 22 / 28 px | −2% |
| Body | 400 | 16 / 26 px | 0 |
| Eyebrow / label | 600 | 11 / 14 px, uppercase | +12% |
| Caption / legal | 400 | 12 / 18 px | 0 |

Flush left. Never centred, never justified — including headlines. Line length stays under 68 characters, which at 16px is roughly the 600px column with 32px side padding.

Weight 800 will fall back to Arial Bold for most readers. Accept it; do not substitute a second font to compensate.

## 3. The mark in email

**SVG does not work in email.** Gmail, Outlook and Yahoo all strip it. Use PNG.

- Header: `lordgen-mark-email-96.png` (82 × 96 px file), displayed at **41 × 48 px** with explicit `width` and `height` attributes.
- Set the wordmark as **live HTML text** beside the mark, not as part of the image. It survives image blocking, it stays readable, and it sidesteps the Archivo rasterisation problem entirely.
- `alt="LordGen AI"` on the mark. Style the alt text gold so a blocked image still reads as brand, not as a broken box.
- Clear space: X = the height of an outer member. At 48px tall the outer member is 24px, so nothing comes within 24px of the mark.
- Minimum size holds: 24px mark, 96px lockup. Below that, the members merge.

**Never** in email: rotation, stretching (always set both dimensions to the true ratio 41:48), rounded corners on the container, gradients, drop shadows.

## 4. Layout

- Content width **600px**, centred on an ink body. Full-bleed background, boxed content.
- Side padding 32px, so the text column is 536px.
- Vertical rhythm in multiples of 8. Section gap 40px, paragraph gap 20px.
- Square containers only, zero border-radius — buttons included. This is the single rule that keeps the emails looking like the brand rather than like Mailchimp.
- Dividers: 1px `#8A6A24`, full column width.

**Anatomy, top to bottom:**

1. **Preheader** — hidden, 40–90 characters, never repeating the subject line.
2. **Header band** — ink, 24px vertical padding, mark left, wordmark text beside it.
3. **Issue bar** — gold 1px rule, then an eyebrow: `ISSUE 001 · 12 AUGUST 2026`, in Slate.
4. **Body** — Leaf headlines, Bone paragraphs.
5. **CTA** — one per issue. Gold block, ink text, 600 weight, 16px, square, 14px × 28px padding.
6. **Footer** — Graphite band, Slate 12px, gold underlined unsubscribe.

## 5. Dark and forced-light modes

The brand is dark-first, which is the harder direction in email — several clients invert or force light backgrounds.

- Put the ink background on a wrapping `<table>` with `bgcolor`, not only in CSS. Clients that strip `<style>` still honour the attribute.
- Add `<meta name="color-scheme" content="dark light">` and `<meta name="supported-color-schemes" content="dark light">`.
- Assume gold may land on white somewhere. It reads at 2.4:1 there — fine for the mark, unusable for text, so never rely on gold alone to carry meaning.
- Test in Outlook desktop, Gmail app on Android (the worst offender for inversion), and Apple Mail dark mode before the demo goes out.

## 6. Compliance furniture

The footer is not optional and it is easy to make ugly. Design it once:

- Legal entity name and a physical postal address.
- Unsubscribe as a visible gold link, not grey-on-grey.
- A one-line reason-for-receipt.

Build every link as a configurable variable (`{{BASE_URL}}/unsubscribe`, `{{BASE_URL}}/archive`) rather than a literal host, so the demo, staging, and production sends all use the same template.

## 7. Files

| File | Format | Use |
|---|---|---|
| `lordgen-ai-logo.svg` | SVG | Master. Web, decks, docs — anywhere but email. |
| `lordgen-mark-816.png` | PNG, 816 × 960, transparent | Source for any raster export you need. |
| `lordgen-mark-email-96.png` | PNG, 82 × 96, transparent | The newsletter header, displayed at 41 × 48. |

The SVG carries live text. Install Archivo (free, Google Fonts) and convert the wordmark to outlines once — after that the file is font-independent and safe to hand anyone.

---

**Not covered here, deliberately:** voice and tone, subject-line style, positioning, data-viz palette, and UI state colours. Those belong to the consultancy identity, and the newsletter demo can ship without them.
