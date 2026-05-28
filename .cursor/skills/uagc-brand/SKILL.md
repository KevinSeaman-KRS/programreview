---
name: uagc-brand
description: Apply UAGC official colors, typography, logos, naming, and editorial rules when building reports, HTML, slides, or marketing artifacts. Use when styling program reports, landing pages, charts, or any UAGC-facing deliverable.
---

# UAGC Brand & Editorial

**Source:** `C:\Users\kseaman\Downloads\uagc_resources.pdf` (Brand Guidelines COM11215, Editorial COM9569, DAL job aid). Guidelines noted as under review (Feb 2026); brand questions: becky.geddie@uagc.edu.

**CSS tokens:** `docs/uagc-brand-tokens.css`

**Approved assets:** IntelligenceBank DAL — https://assets.arizona.edu/ (NetID). Logos only from DAL; do not recreate Block A.

## Colors (use HEX in web)

| Name | HEX | Use |
|------|-----|-----|
| Arizona Red | `#AB0520` | Primary accent, funnel progression, CTAs |
| Arizona Blue | `#0C234B` | Headings, table headers, dark UI |
| Highlight Blue | `#0076A8` | Links in dashboards (prefer over `#0000ff` for UI) |
| Sky | `#81D3EB` | Charts/secondary fills |
| Dark Gray | `#53565A` | Body text |
| Light Gray | `#D0D0CE` | Borders, backgrounds |
| Silver | `#98A4AE` | Muted labels |

**Do not:** combine Orange `#EF9600` or Yellow `#F9E17D` with Arizona Red on the same layout.

**Wrong (legacy in old POCs):** `#CC0033`, `#1a1a2e` — not official brand reds/blues.

## Typography

| Context | Font |
|---------|------|
| Web / HTML reports | **Montserrat** (Google Fonts) — Regular, Medium, Bold |
| Microsoft Office / email | Calibri |
| Advertising (Adobe CC) | Proxima Nova; Extra Condensed **headlines only** |

Load Montserrat:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## Naming

- First reference: **the University of Arizona Global Campus**
- Second reference: **UAGC** (preferred over “Global Campus”)
- Standalone titles/footers: **The University of Arizona Global Campus**
- Never: “UA Global Campus”, possessive **UAGC's** / **Global Campus'** — rephrase
- Never: “Global” alone

## Logos (summary)

- Horizontal full-color default for web; reversed on photos with contrast
- Digital ads: full-color Block A for accessibility
- Block A never alone, never in words, never altered
- Minimum horizontal logo width: 115px (web) / 1.625″ print
- Clear space ≥ width of top blue bar on Block A
- Two Block A logos in one creative: **not approved**

## Voice (short)

Real & authentic, empathetic & welcoming, empowering & celebratory, clear & concise. Avoid elitist, stuffy, pushy tone.

## Editorial quick rules

- Oxford comma; single space after periods
- No possessive UAGC; spell out states alone; abbreviate with cities (`Chandler, AZ`)
- Times: `4 p.m.`, `8:35 a.m. PT` (student comms); catalog/deadlines: **MT**
- Hyperlinks in prose: `#0000ff` per editorial guide
- Emphasis: **bold** or Arizona Blue text — not ALL CAPS
- Degrees: spell out on first mention (except MBA); no `UAGC's program`

## MAC / external materials

External-facing reports and collateral need MAC review (~10 business days). Marketing analytics HTML for internal use should still follow brand visuals.

## Report implementation checklist

1. Set `:root` from `docs/uagc-brand-tokens.css`
2. `font-family: var(--font-sans)`
3. Replace legacy `#CC0033` / `#1a1a2e`
4. Table headers: Arizona Blue; accent bars: Arizona Red
5. Do not add box shadows (aligns with frontend-skill / brand flat surfaces)
