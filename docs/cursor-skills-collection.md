# Cursor Skills Collection

A reference doc for sharing skills across Cursor setups. Copy any skill block below into a folder at `~/.cursor/skills/<skill-name>/SKILL.md` (personal) or `.cursor/skills/<skill-name>/SKILL.md` (project-scoped).

> **Cursor built-in skills** (marked ⚙️ below) live in `~/.cursor/skills-cursor/` — Cursor manages these automatically. You already have them. The custom skills (marked ★) need manual installation.

---

## Table of Contents

### Cursor Built-in Skills ⚙️
1. [babysit](#babysit) — Keep a PR merge-ready in a loop
2. [canvas](#canvas) — Create live React artifact canvases beside chat
3. [create-hook](#create-hook) — Create Cursor hooks (hooks.json + scripts)
4. [create-rule](#create-rule) — Create `.cursor/rules/*.mdc` files
5. [create-skill](#create-skill) — Author new SKILL.md files
6. [create-subagent](#create-subagent) — Create custom `.cursor/agents/*.md` subagents
7. [migrate-to-skills](#migrate-to-skills) — Convert rules/commands to skills format
8. [sdk](#sdk) — Build integrations with the `@cursor/sdk` TypeScript SDK
9. [shell](#shell) — Run literal shell commands via `/shell`
10. [split-to-prs](#split-to-prs) — Split a branch into small reviewable PRs
11. [statusline](#statusline) — Configure CLI status line above the prompt
12. [update-cli-config](#update-cli-config) — Edit `~/.cursor/cli-config.json`
13. [update-cursor-settings](#update-cursor-settings) — Edit Cursor `settings.json`

### Custom Skills ★
14. [doc](#doc) — Create/edit `.docx` documents with python-docx
15. [frontend-skill](#frontend-skill) — Ship premium, image-led UI and landing pages
16. [imagegen](#imagegen) — Generate/edit images via OpenAI Image API
17. [openai-docs](#openai-docs) — Fetch authoritative OpenAI developer docs
18. [playwright](#playwright) — Automate browsers via `playwright-cli`
19. [ui-ux-pro-max](#ui-ux-pro-max) — Searchable design system DB (67 styles, 96 palettes, 57 font pairings)

---

## Installation

```bash
# Personal skill (available across all your projects)
mkdir -p ~/.cursor/skills/<skill-name>
# Paste SKILL.md content below into ~/.cursor/skills/<skill-name>/SKILL.md

# Project skill (checked into version control, shared with team)
mkdir -p .cursor/skills/<skill-name>
# Paste SKILL.md content into .cursor/skills/<skill-name>/SKILL.md
```

---

---

## Cursor Built-in Skills ⚙️

> These are managed automatically by Cursor. You already have them at `~/.cursor/skills-cursor/`. Listed here for reference only.

---

### babysit

**Trigger:** Use when asked to keep a PR merge-ready or monitor CI in a loop.

```markdown
---
name: babysit
description: >-
  Keep a PR merge-ready by triaging comments, resolving clear conflicts, and
  fixing CI in a loop.
---
# Babysit PR
Your job is to get this PR to a merge-ready state.

Check PR status, comments, and latest CI and resolve any issues until the PR is ready to merge.

1. Merge conflicts: Intelligently resolve any merge conflicts, preserving the intent and correctness of changes on your branch and the base branch. If intents conflict, abort the merge and ask for clarification.
2. Comments: Review active unresolved comments (including Bugbot) and resolve change requests / bug reports where valid. When fetching GitHub comments, filter out resolved threads first. Read only each comment body and the minimum location/URL needed to act on it; do not read the entire JSON output or other unnecessary payload data. Carefully validate issues reported by Bugbot and only take action on those that are valid; explain when you disagree or are unsure.
3. CI: Fix CI issues caused by changes within this PR's scope. Never change CI checks/workflows just to make failures pass, or make unrelated code changes; if that would be required, report back instead. For merge-blocking failures that seem unrelated to this PR, check whether the branch is behind the base branch and merge latest changes, since another PR may have fixed them. Push scoped fixes and re-watch CI until mergeable + green + comments triaged.
```

---

### canvas

**Trigger:** Use when producing standalone analytical artifacts — tables, charts, data analyses, billing/security reports, structured MCP tool output.

```markdown
---
name: canvas
description: >-
  A Cursor Canvas is a live React app that the user can open beside the chat.
  You MUST use a canvas when the agent produces a standalone analytical artifact
  — quantitative analyses, billing investigations, security audits, architecture
  reviews, data-heavy content, timelines, charts, tables, interactive
  explorations, repeatable tools, or any response that benefits from visual
  layout. Especially prefer a canvas when presenting results from MCP tools
  (Datadog, Databricks, Linear, Sentry, Slack, etc.) where the data is the
  deliverable — render it in a rich canvas rather than dumping it into a
  markdown table or code block. If you catch yourself about to write a markdown
  table, stop and use a canvas instead. You MUST also read this skill whenever
  you create, edit, or debug any .canvas.tsx file.
metadata:
  surfaces:
    - ide
---
# Canvas Skill
[Full content in ~/.cursor/skills-cursor/canvas/SKILL.md]
```

---

### create-hook

**Trigger:** Use when creating Cursor hooks (hooks.json), writing hook scripts, or automating behavior around agent events.

```markdown
---
name: create-hook
description: >-
  Create Cursor hooks. Use when you want to create a hook, write hooks.json, add
  hook scripts, or automate behavior around agent events.
---
# Creating Cursor Hooks
[Full content in ~/.cursor/skills-cursor/create-hook/SKILL.md]
```

---

### create-rule

**Trigger:** Use when creating `.cursor/rules/*.mdc` files, adding coding standards, or managing project conventions.

```markdown
---
name: create-rule
description: >-
  Create Cursor rules for persistent AI guidance. Use when you want to create a
  rule, add coding standards, set up project conventions, configure
  file-specific patterns, create RULE.md files, or asks about .cursor/rules/ or
  AGENTS.md.
---
# Creating Cursor Rules
[Full content in ~/.cursor/skills-cursor/create-rule/SKILL.md]
```

---

### create-skill

**Trigger:** Use when authoring a new SKILL.md or asking about skill structure.

```markdown
---
name: create-skill
description: >-
  Create Cursor Agent Skills. Use when authoring a new skill or asking about
  SKILL.md structure.
---
# Creating Skills in Cursor
[Full content in ~/.cursor/skills-cursor/create-skill/SKILL.md]
```

---

### create-subagent

**Trigger:** Use when creating custom subagents in `.cursor/agents/` or `~/.cursor/agents/`.

```markdown
---
name: create-subagent
description: >-
  Create custom subagents for specialized AI tasks. Use when you want to create
  a new type of subagent, set up task-specific agents, configure code reviewers,
  debuggers, or domain-specific assistants with custom prompts.
disable-model-invocation: true
---
# Creating Custom Subagents
[Full content in ~/.cursor/skills-cursor/create-subagent/SKILL.md]
```

---

### migrate-to-skills

**Trigger:** Use when converting "Applied intelligently" Cursor rules or slash commands to Agent Skills format.

```markdown
---
name: migrate-to-skills
description: >-
  Convert 'Applied intelligently' Cursor rules (.cursor/rules/*.mdc) and slash
  commands (.cursor/commands/*.md) to Agent Skills format (.cursor/skills/).
disable-model-invocation: true
---
# Migrate Rules and Slash Commands to Skills
[Full content in ~/.cursor/skills-cursor/migrate-to-skills/SKILL.md]
```

---

### sdk

**Trigger:** Use when building with `@cursor/sdk`, running Cursor agents from scripts/CI, or wiring Cursor into automation.

```markdown
---
name: sdk
description: >-
  Guide users building apps, scripts, CI pipelines, or automations on top of the
  Cursor TypeScript SDK (`@cursor/sdk`). Use when the user mentions integrating,
  installing, or writing code against the Cursor SDK; says `Agent.create`,
  `Agent.prompt`, `Agent.resume`, `agent.send`, `run.stream`,
  `CursorAgentError`, or `@cursor/sdk`; asks to run Cursor agents
  programmatically from a script, CI/CD pipeline, GitHub Action, backend
  service, or other code outside the Cursor IDE.
---
# Cursor SDK
[Full content in ~/.cursor/skills-cursor/sdk/SKILL.md]
```

---

### shell

**Trigger:** Only when user explicitly invokes `/shell` followed by a literal command.

```markdown
---
name: shell
description: >-
  Runs the rest of a /shell request as a literal shell command. Use only when
  the user explicitly invokes /shell and wants the following text executed
  directly in the terminal.
disable-model-invocation: true
---
# Run Shell Commands
Use this skill only when the user explicitly invokes `/shell`.

1. Treat all user text after `/shell` as the literal shell command to run.
2. Execute it immediately. Do not rewrite or improve it.
3. If `/shell` has no following text, ask which command to run.

After running: briefly report exit status and any important stdout/stderr.
```

---

### split-to-prs

**Trigger:** Use when the user asks to split a chat, set of changes, branch, or PR into smaller reviewable units.

```markdown
---
name: split-to-prs
description: >-
  Split current work into small reviewable PRs. Use when the user asks to split
  a chat, set of changes, branch, or PR.
---
# Split to PRs
[Full content in ~/.cursor/skills-cursor/split-to-prs/SKILL.md]
```

---

### statusline

**Trigger:** Use when the user mentions status line, statusLine, CLI status bar, or prompt footer customization.

```markdown
---
name: statusline
description: >-
  Configure a custom status line in the CLI. Use when the user mentions status
  line, statusline, statusLine, CLI status bar, prompt footer customization, or
  wants to add session context above the prompt.
---
# CLI Status Line

Add `statusLine` to `~/.cursor/cli-config.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.cursor/statusline.sh",
    "padding": 2
  }
}
```

[Full content including stdin payload schema and examples in ~/.cursor/skills-cursor/statusline/SKILL.md]
```

---

### update-cli-config

**Trigger:** Use when the user wants to change CLI settings, configure permissions, switch approval mode, enable vim mode, or toggle display options.

```markdown
---
name: update-cli-config
description: >-
  View and modify Cursor CLI configuration settings in
  ~/.cursor/cli-config.json. Use when the user wants to change CLI settings,
  configure permissions, switch approval mode, enable vim mode, toggle display
  options, configure sandbox, or manage any CLI preferences.
metadata:
  surfaces:
    - cli
---
# Cursor CLI Configuration
Config file: `~/.cursor/cli-config.json`

Key settings: `permissions` (allow/deny patterns), `editor.vimMode`, `display.showLineNumbers`,
`approvalMode` ("allowlist"|"unrestricted"), `sandbox.mode`, `maxMode`, `attribution`.

[Full content in ~/.cursor/skills-cursor/update-cli-config/SKILL.md]
```

---

### update-cursor-settings

**Trigger:** Use when the user wants to change editor settings, themes, font size, tab size, format on save, keybindings, or any settings.json values.

```markdown
---
name: update-cursor-settings
description: >-
  Modify Cursor/VSCode user settings in settings.json. Use when you want to
  change editor settings, preferences, configuration, themes, font size, tab
  size, format on save, auto save, keybindings, or any settings.json values.
metadata:
  surfaces:
    - ide
---
# Updating Cursor Settings
Settings file locations:
- macOS: ~/Library/Application Support/Cursor/User/settings.json
- Linux: ~/.config/Cursor/User/settings.json
- Windows: %APPDATA%\Cursor\User\settings.json

[Full content in ~/.cursor/skills-cursor/update-cursor-settings/SKILL.md]
```

---

---

## Custom Skills ★

> These need manual installation. Copy the full SKILL.md block into the path shown.

---

### doc

**Install path:** `~/.cursor/skills/doc/SKILL.md`

```markdown
---
name: "doc"
description: "Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks."
---

# DOCX Skill

## When to use
- Read or review DOCX content where layout matters (tables, diagrams, pagination).
- Create or edit DOCX files with professional formatting.
- Validate visual layout before delivery.

## Workflow
1. Prefer visual review (layout, tables, diagrams).
   - If `soffice` and `pdftoppm` are available, convert DOCX -> PDF -> PNGs.
   - Or use `scripts/render_docx.py` (requires `pdf2image` and Poppler).
2. Use `python-docx` for edits and structured creation (headings, styles, tables, lists).
3. After each meaningful change, re-render and inspect the pages.
4. If visual review is not possible, extract text with `python-docx` as a fallback.
5. Keep intermediate outputs organized and clean up after final approval.

## Temp and output conventions
- Use `tmp/docs/` for intermediate files; delete when done.
- Write final artifacts under `output/doc/`.

## Dependencies
```bash
uv pip install python-docx pdf2image
brew install libreoffice poppler  # macOS
```

## Rendering commands
```bash
# DOCX -> PDF
soffice --headless --convert-to pdf --outdir $OUTDIR $INPUT_DOCX

# PDF -> PNGs
pdftoppm -png $OUTDIR/$BASENAME.pdf $OUTDIR/$BASENAME

# Bundled helper
python3 scripts/render_docx.py /path/to/file.docx --output_dir /tmp/docx_pages
```

## Quality expectations
- Consistent typography, spacing, margins, and clear hierarchy.
- No clipped/overlapping text, broken tables, or unreadable characters.
- ASCII hyphens only — avoid U+2011 and other Unicode dashes.
- Citations must be human-readable; never leave tool tokens or placeholders.

## Final checks
- Re-render every page at 100% zoom before delivery.
- Fix spacing/alignment/pagination issues and repeat the render loop.
```

---

### frontend-skill

**Install path:** `~/.cursor/skills/frontend-skill/SKILL.md`

```markdown
---
name: frontend-skill
description: Use when the task asks for a visually strong landing page, website, app, prototype, demo, or game UI. This skill enforces restrained composition, image-led hierarchy, cohesive content structure, and tasteful motion while avoiding generic cards, weak branding, and UI clutter.
---

# Frontend Skill

Goal: ship interfaces that feel deliberate, premium, and current. Default toward award-level
composition: one big idea, strong imagery, sparse copy, rigorous spacing, a small number of
memorable motions.

## Page Taxonomy

| Type | Examples | Key principles |
|------|----------|----------------|
| **Marketing / Landing** | Homepage, campaign, signup | Full-bleed hero, image-led, poster first viewport |
| **Product / App** | Dashboard, settings, analytics | Utility copy, calm surface, cards only when interactive |
| **Immersive / Narrative** | Simulation arena, game UI | Different visual thesis allowed (playful, high contrast) |
| **Insight / Storytelling** | Brand perception, exec reports | Two layers: instrumentation + interpretation |

## Working Model

Before building, write three things:
- **visual thesis**: one sentence on mood, material, and energy
- **content plan**: hero → support → detail → final CTA
- **interaction thesis**: 2–3 motion ideas that change the feel

## Beautiful Defaults

- Start with composition, not components.
- Prefer full-bleed hero or full-canvas visual anchor (marketing only; apps use constrained layouts).
- Make brand/product name the loudest text.
- Default to **cardless layouts** — sections, columns, dividers, lists, media blocks.
- Limit the system: two typefaces max, one accent color by default.
- Treat first viewport as a poster (marketing) or command surface (apps).

## Landing Pages — Default Sequence

1. Hero: brand/product, promise, CTA, dominant visual
2. Support: one concrete feature, offer, or proof point
3. Detail: atmosphere, workflow, product depth, or story
4. Final CTA: convert, start, visit, or contact

**Hero rules:**
- Full-bleed image, edge-to-edge, no inherited gutters on branded landing pages.
- No hero cards, stat strips, logo clouds, pill soup, or floating dashboards by default.
- All text over imagery must maintain strong contrast.
- If the first viewport still works after removing the image, the image is too weak.

## Apps — Linear-style Restraint

- Calm surface hierarchy, strong typography, few colors, dense-but-readable.
- Cards only when the card is the interaction (selectable, draggable, independently actionable).
- Avoid: dashboard-card mosaics, thick borders on every region, decorative gradients, ornamental icons.

## Imagery

- At least one strong, real-looking image for brands/editorial/lifestyle pages.
- Prefer in-situ photography over abstract gradients or fake 3D objects.
- Do not use images with embedded signage or typographic clutter.

## Forbidden Patterns

- Gradients as background texture
- Emoji as icons or bullets
- Box shadows (flat surfaces only)
- Wall of identical cards with no variation
- Rainbow coloring (color is used sparingly with purpose)
- Giant text above H1 (24px)
- Decorative colored borders on every element
```

---

### imagegen

**Install path:** `~/.cursor/skills/imagegen/SKILL.md`

```markdown
---
name: "imagegen"
description: "Use when the user asks to generate or edit images via the OpenAI Image API (for example: generate image, edit/inpaint/mask, background removal or replacement, transparent background, product shots, concept art, covers, or batch variants); run the bundled CLI (`scripts/image_gen.py`) and require `OPENAI_API_KEY` for live calls."
---

# Image Generation Skill

Generate and edit images via the OpenAI Image API using `scripts/image_gen.py`.

## Quick Start

```bash
# Requires OPENAI_API_KEY
export OPENAI_API_KEY="sk-..."

# Generate
python3 scripts/image_gen.py generate --prompt "minimal product photo of a ceramic mug"

# Edit (inpaint)
python3 scripts/image_gen.py edit --image input.png --mask mask.png --prompt "replace background with warm sunset"

# Batch
python3 scripts/image_gen.py batch --prompts prompts.txt --n 4
```

## Prompt Structure

Scene → Subject → Details → Constraints

```
Use case: product-photography
Asset type: landing page hero
Primary request: a minimal ceramic coffee mug
Style/medium: clean product photography
Composition: centered product, generous negative space on right
Lighting: soft studio lighting
Constraints: no logos, no text, no watermark
```

## Best Practices

- For photorealism, use camera/composition language.
- Quote exact text for typographic elements and specify placement.
- For edits, repeat invariants every iteration to prevent drift.
- Start with `quality=low` for speed; use `quality=high` for text-heavy outputs.
- Add `"Avoid: stock-photo vibe, cheesy lens flare, oversaturation"` to prevent "tacky" outputs.

## References

- CLI commands: `references/cli.md`
- API parameters: `references/image-api.md`
- Prompting principles: `references/prompting.md`
- Sample prompts: `references/sample-prompts.md`
```

---

### openai-docs

**Install path:** `~/.cursor/skills/openai-docs/SKILL.md`

```markdown
---
name: "openai-docs"
description: "Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations (for example: Codex, Responses API, Chat Completions, Apps SDK, Agents SDK, Realtime, model capabilities or limits); prioritize OpenAI docs MCP tools and restrict any fallback browsing to official OpenAI domains."
---

# OpenAI Docs

Provide authoritative, current guidance from OpenAI developer docs.

## Quick Start

- `mcp__openaiDeveloperDocs__search_openai_docs` — find relevant doc pages
- `mcp__openaiDeveloperDocs__fetch_openai_doc` — pull exact sections
- `mcp__openaiDeveloperDocs__list_openai_docs` — browse/discover pages

Always use MCP doc tools before web search for OpenAI-related questions.

## Product Snapshots

1. **Apps SDK**: ChatGPT apps via web component UI + MCP server
2. **Responses API**: Unified stateful, multimodal, tool-using endpoint
3. **Chat Completions API**: Generate responses from a message list
4. **Codex**: OpenAI's coding agent (write, understand, review, debug code)
5. **gpt-oss**: Open-weight models (120b, 20b) under Apache 2.0
6. **Realtime API**: Low-latency speech-to-speech conversations
7. **Agents SDK**: Toolkit for agents with tools, handoffs, streaming, tracing

## Workflow

1. Clarify product scope (Codex, OpenAI API, or ChatGPT Apps SDK)
2. Search docs with a precise query
3. Fetch the best page and specific section (use `anchor` when possible)
4. Answer with concise guidance and cite the doc source

## Quality Rules

- Treat OpenAI docs as source of truth; avoid speculation.
- If docs don't cover the user's need, say so and offer next steps.
- When falling back to web, restrict to `developers.openai.com` / `platform.openai.com`.
```

---

### playwright

**Install path:** `~/.cursor/skills/playwright/SKILL.md`

```markdown
---
name: "playwright"
description: "Use when the task requires automating a real browser from the terminal (navigation, form filling, snapshots, screenshots, data extraction, UI-flow debugging) via `playwright-cli` or the bundled wrapper script."
---

# Playwright CLI Skill

Drive a real browser from the terminal using `playwright-cli`. CLI-first automation — do not
pivot to `@playwright/test` unless the user explicitly asks for test files.

## Prerequisite

```bash
command -v npx >/dev/null 2>&1  # npx required for wrapper
npm install -g @playwright/cli@latest  # optional global install
```

## Quick Start

```bash
export PWCLI="$HOME/.codex/skills/playwright/scripts/playwright_cli.sh"

"$PWCLI" open https://example.com --headed
"$PWCLI" snapshot          # get element refs
"$PWCLI" click e15         # use refs from latest snapshot
"$PWCLI" type "Hello"
"$PWCLI" press Enter
"$PWCLI" screenshot
```

## Core Workflow

1. Open the page.
2. Snapshot to get stable element refs.
3. Interact using refs from the latest snapshot.
4. Re-snapshot after navigation or significant DOM changes.

## Recommended Patterns

```bash
# Form fill and submit
"$PWCLI" open https://example.com/form
"$PWCLI" snapshot
"$PWCLI" fill e1 "user@example.com"
"$PWCLI" fill e2 "password123"
"$PWCLI" click e3
"$PWCLI" snapshot

# Traces for debugging
"$PWCLI" open https://example.com --headed
"$PWCLI" tracing-start
# ...interactions...
"$PWCLI" tracing-stop
```

## Guardrails

- Always snapshot before referencing element IDs like `e12`.
- Re-snapshot when refs seem stale.
- Prefer explicit commands over `eval` and `run-code`.
- Use `--headed` when a visual check will help.
- Save artifacts under `output/playwright/`.
```

---

### ui-ux-pro-max

> **⚠️ This skill cannot be copy-pasted.** It is a database-backed tool with ~62 KB of Python scripts and 26 CSV data files. A markdown stub is not enough to use it. **Request the complete directory from Omar ([@ocorral](https://github.com/ocorral))** — ask for the full `ui-ux-pro-max/` folder and drop it into `.cursor/skills/`.

**Why it's worth requesting:** This is the highest-impact skill for redesigning any UI. It gives the agent a searchable database covering palettes, typography pairings, chart types, UX guidelines, and stack-specific patterns — all queryable via CLI in seconds before writing a single line of code.

**Full directory structure (what to ask for):**

```
.cursor/skills/ui-ux-pro-max/
├── SKILL.md                          # Agent instructions + workflow
├── scripts/
│   ├── search.py                     # CLI entry point (~5.5 KB)
│   ├── core.py                       # Search engine (~13 KB)
│   └── design_system.py              # Design system aggregator (~43 KB)
└── data/
    ├── charts.csv                    # 25 chart types
    ├── colors.csv                    # 96 color palettes
    ├── icons.csv                     # icon recommendations
    ├── landing.csv                   # landing page patterns
    ├── products.csv                  # product type → design mapping
    ├── react-performance.csv         # React perf patterns
    ├── styles.csv                    # 67 UI styles
    ├── typography.csv                # 57 font pairings
    ├── ui-reasoning.csv              # 100 reasoning rules
    ├── ux-guidelines.csv             # 99 UX guidelines
    ├── web-interface.csv             # web interface patterns
    └── stacks/
        ├── html-tailwind.csv
        ├── react.csv
        ├── nextjs.csv
        ├── vue.csv / nuxtjs.csv / nuxt-ui.csv
        ├── svelte.csv
        ├── shadcn.csv
        ├── swiftui.csv
        ├── react-native.csv
        ├── flutter.csv
        ├── jetpack-compose.csv
        ├── reflex.csv
        └── astro.csv
```

**Key commands once installed:**

```bash
# Generate a complete design system (always start here)
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "beauty spa wellness service" --design-system -p "Project Name"

# Domain-specific searches
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "glassmorphism dark" --domain style
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "animation accessibility" --domain ux
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "real-time analytics" --domain chart

# Stack-specific guidelines
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "layout responsive" --stack html-tailwind
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "state management" --stack reflex

# Persist for hierarchical page-level overrides (Master + page files)
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "fintech dashboard" --design-system --persist -p "MyApp"
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "checkout flow" --design-system --persist -p "MyApp" --page "checkout"
```

**Available search domains:** `product`, `style`, `typography`, `color`, `landing`, `chart`, `ux`, `react`, `web`

**Available stacks:** `html-tailwind`, `react`, `nextjs`, `vue`, `svelte`, `swiftui`, `react-native`, `flutter`, `shadcn`, `jetpack-compose`, `reflex`, `astro`, `nuxtjs`, `nuxt-ui`

---

## Quick Cheatsheet

| Skill | What it does | When it activates |
|-------|-------------|-------------------|
| `babysit` | PR triage + CI fix loop | "keep this PR green", "babysit my PR" |
| `canvas` | Live React artifact beside chat | any data-heavy response, tables, charts |
| `create-hook` | hooks.json + scripts | "create a hook", "add a pre-commit hook" |
| `create-rule` | .cursor/rules/*.mdc | "add a rule", "set coding standard" |
| `create-skill` | new SKILL.md | "create a skill", "make a skill for X" |
| `create-subagent` | .cursor/agents/*.md | "create a subagent", "make a code reviewer agent" |
| `migrate-to-skills` | rules/commands → skills | "migrate my rules to skills" |
| `sdk` | @cursor/sdk integrations | "Cursor SDK", "Agent.create", "CI agent" |
| `shell` | literal `/shell` execution | user types `/shell <command>` |
| `split-to-prs` | split branch into small PRs | "split this into PRs" |
| `statusline` | CLI status bar above prompt | "status line", "CLI footer" |
| `update-cli-config` | ~/.cursor/cli-config.json | "yolo mode", "vim mode", "allow all tools" |
| `update-cursor-settings` | Cursor settings.json | "change font", "format on save", "dark theme" |
| `doc` ★ | python-docx DOCX editing | ".docx", "Word document", "format fidelity" |
| `frontend-skill` ★ | premium UI/landing pages | "landing page", "website", "app UI" |
| `imagegen` ★ | OpenAI image generation | "generate image", "edit image", "product shot" |
| `openai-docs` ★ | authoritative OpenAI docs | "Codex API", "Responses API", "Agents SDK" |
| `playwright` ★ | browser automation from terminal | "automate browser", "playwright", "scrape" |
| `ui-ux-pro-max` ★ | design system DB + CLI | "design system", "color palette", "font pairing", "UI/UX" |

---

*Generated from a live Cursor workspace. Last updated: May 2026.*
