# Cursor SDK in this workspace

## What it does here

`npm run qa:outliers` runs a **local** Cursor agent that:

1. Reads `qa_outlier_programs.json` (rows flagged before publishing program reports).
2. Uses the **BigQuery MCP** (same stack as IDE chat) to validate counts against `advertising-data-mart.inquiries.vw_lead_extract_details`.
3. Writes `docs/sdk-qa-outliers.md` with pass/warn/fail and recommended fixes.

That turns “ask the agent in chat to double-check outliers” into a **repeatable command** you can run before regenerating `program_report.html`.

## Setup

```powershell
# API key: https://cursor.com/dashboard/cloud-agents
$env:CURSOR_API_KEY = "cursor_..."

# BigQuery (if not already): gcloud auth application-default login
cd C:\Users\kseaman\Downloads\Cursor
npm run qa:outliers
```

## Why SDK vs only using chat

| Chat in IDE | `npm run qa:outliers` (SDK) |
|-------------|-----------------------------|
| Ad hoc, human-in-the-loop | Scriptable, same prompt every time |
| Hard to gate CI / pre-deploy | Exit codes: 0 finished, 1 startup, 2 run error |
| No log of agent/run IDs | Logs `agentId` and `runId` for dashboard follow-up |

Implementation: `scripts/verify-outliers-sdk.ts` (`Agent.create` + stream + `wait`, explicit MCP + `settingSources: ["user"]`).
