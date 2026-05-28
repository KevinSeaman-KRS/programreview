# AGENTS.md

> **Context cap:** Keep this file under ~60 lines. Add detail to docs/agent-context/*.md, not here.

## Stack

[YOUR STACK HERE - e.g. "Next.js + FastAPI, Python 3.12, deployed to AWS"]

## Learned User Preferences

- No mock data - use real data only; when unavailable, show empty states with instructions to connect the data source
- Design before build - present 2-3 approaches with trade-offs, get approval, then implement
- Verify before declaring done - run tests, lints, and imports; show concrete evidence
- Parallel agents for independent work - dispatch concurrent agents instead of sequential
- No hardcoded paths - use helper functions or env vars
- Use logger (debug/warning/error), not print(); avoid bare except:
- Signal over spectacle - every visual element must answer "what decision does this help the user make?"
- Maximum agent fleet - dispatch max parallel agents per request; only serialize when there are true dependencies

## Learned Workspace Facts

[Add project-specific facts as you work - API quirks, deploy commands, gotchas, etc.]

Domain-specific facts live in docs/agent-context/ - load the file that matches your task.
