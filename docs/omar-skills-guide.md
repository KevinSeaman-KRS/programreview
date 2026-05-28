# Omar's skills collection — how it maps here

**Source file:** `C:\Users\kseaman\Downloads\cursor-skills-collection 1.md`  
**In-repo copy:** `docs/cursor-skills-collection.md`

## Already on your machine (Cursor built-ins ⚙️)

These live in `%USERPROFILE%\.cursor\skills-cursor\`. Cursor loads them automatically — no install.

| Skill | Useful here when… |
|-------|-------------------|
| **canvas** | Program report metrics, funnel tables, BigQuery/MCP output |
| **sdk** | `npm run qa:outliers`, `scripts/verify-outliers-sdk.ts` |
| **babysit** | PRs for `deploy/` or report pipeline repos |
| **create-rule** / **create-skill** | Extending `.cursor/rules/` or skills |
| **split-to-prs** | Splitting large report/HTML changes into reviewable PRs |

## Personal skills (★ → `%USERPROFILE%\.cursor\skills\`)

| Skill | Status |
|-------|--------|
| doc | Installed |
| frontend-skill | Installed |
| imagegen | Installed (CLI needs `scripts/image_gen.py` from Omar) |
| openai-docs | Installed |
| playwright | Installed |

## Project skills (`.cursor/skills/`)

| Skill | Purpose |
|-------|---------|
| **sql-query** | BigQuery / SQL Server lead data |
| **uagc-brand** | Official colors, fonts, naming (`uagc_resources.pdf`) |
| **ui-ux-pro-max** | **Stub only** — see below |

## ui-ux-pro-max — action required

Omar's updated doc makes this explicit: **you cannot paste markdown and use the skill.** You need the full directory (~62 KB Python + 26 CSVs).

1. Ask Omar ([@ocorral](https://github.com/ocorral)) for the complete `ui-ux-pro-max/` folder.
2. Replace `.cursor/skills/ui-ux-pro-max/` (drop in `scripts/`, `data/`, and real `SKILL.md`).
3. Run a design-system query before the next report UI pass:

```bash
python .cursor/skills/ui-ux-pro-max/scripts/search.py "higher ed analytics dashboard professional" --design-system -p "UAGC Program Report"
```

**New in Omar's update:** full tree listing (`ui-reasoning.csv`, `astro` / `nuxtjs` stacks), `--persist --page` workflow, and persist commands for page-level overrides.

## Suggested pairing for this workspace

1. **sql-query** + **canvas** → analytics answers  
2. **uagc-brand** + **frontend-skill** → on-brand report HTML (done for colors/fonts)  
3. **uagc-brand** + **ui-ux-pro-max** (when installed) → roadmap redesign with compliant palette search  
4. **playwright** + `playwright.config.ts` → debug captures before batch runs  
5. **sdk** → `npm run qa:outliers`

## Refresh personal skills from Omar

If Omar ships a newer `cursor-skills-collection *.md`, diff the ★ skill blocks and overwrite `%USERPROFILE%\.cursor\skills\<name>\SKILL.md`. Built-ins (⚙️) are managed by Cursor — no copy needed.
