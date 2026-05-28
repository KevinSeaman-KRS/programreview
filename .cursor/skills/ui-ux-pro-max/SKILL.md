---
name: ui-ux-pro-max
description: >-
  Searchable design system database (67 styles, 96 palettes, 57 font pairings, 99 UX
  guidelines, 25 chart types). Use for UI/UX design, landing pages, colors, typography,
  or design systems. Requires the full skill directory from Omar — not installable from
  markdown alone.
---

# ui-ux-pro-max (stub — install full package)

**This folder is a placeholder.** The skill needs Python scripts and CSV data (~62 KB). Request the complete directory from Omar ([@ocorral](https://github.com/ocorral)): the full `ui-ux-pro-max/` folder with `scripts/` and `data/`.

Replace this stub by dropping Omar's package here:

```
.cursor/skills/ui-ux-pro-max/
├── SKILL.md
├── scripts/
│   ├── search.py
│   ├── core.py
│   └── design_system.py
└── data/
    ├── charts.csv, colors.csv, icons.csv, landing.csv, products.csv
    ├── react-performance.csv, styles.csv, typography.csv
    ├── ui-reasoning.csv, ux-guidelines.csv, web-interface.csv
    └── stacks/   (html-tailwind, react, nextjs, vue, svelte, shadcn, …)
```

## Why request it

Highest-impact skill for redesigning `program_report.html`, Sankey POCs, and dashboards. Query palettes, typography, charts, and stack patterns via CLI before writing HTML/CSS.

Pair with **uagc-brand** (official UAGC colors/fonts) — ui-ux-pro-max suggests systems; uagc-brand constrains to brand compliance.

## Commands (after full install)

```bash
# Start every UI task with a design system
python .cursor/skills/ui-ux-pro-max/scripts/search.py "higher ed analytics dashboard" --design-system -p "UAGC Program Report"

python .cursor/skills/ui-ux-pro-max/scripts/search.py "data visualization funnel" --domain chart
python .cursor/skills/ui-ux-pro-max/scripts/search.py "layout responsive" --stack html-tailwind
python .cursor/skills/ui-ux-pro-max/scripts/search.py "accessibility tables" --domain ux

# Persist master + page overrides
python .cursor/skills/ui-ux-pro-max/scripts/search.py "program detail page" --design-system --persist -p "UAGC Program Report" --page "detail"
```

**Domains:** `product`, `style`, `typography`, `color`, `landing`, `chart`, `ux`, `react`, `web`

**Stacks:** `html-tailwind`, `react`, `nextjs`, `vue`, `nuxtjs`, `nuxt-ui`, `svelte`, `shadcn`, `swiftui`, `react-native`, `flutter`, `jetpack-compose`, `reflex`, `astro`

## Reference

Omar's catalog: `docs/cursor-skills-collection.md` (from `cursor-skills-collection 1.md`).
