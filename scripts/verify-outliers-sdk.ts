#!/usr/bin/env node
/**
 * Pre-publish QA: validate qa_outlier_programs.json against BigQuery.
 *
 * Uses @cursor/sdk (local runtime) with the same BigQuery MCP as Cursor IDE.
 *
 * Prerequisites:
 *   export CURSOR_API_KEY="cursor_..."   # https://cursor.com/dashboard/cloud-agents
 *   gcloud auth application-default login  # BigQuery MCP credentials
 *
 * Usage:
 *   npm run qa:outliers
 */

import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { Agent, CursorAgentError } from "@cursor/sdk";

const ROOT = process.cwd();
const OUTLIERS_PATH = path.join(ROOT, "qa_outlier_programs.json");
const SKILL_PATH = path.join(ROOT, ".cursor", "skills", "sql-query", "SKILL.md");
const REPORT_PATH = path.join(ROOT, "docs", "sdk-qa-outliers.md");

const mcpServers = {
  bigquery: {
    type: "stdio" as const,
    command: "uvx",
    args: [
      "--from",
      "mcp-server-bigquery",
      "mcp-server-bigquery",
      "--project",
      "advertising-data-mart",
      "--location",
      "US",
    ],
  },
};

function buildPrompt(outliersJson: string, skillExcerpt: string): string {
  return `You are running unattended pre-publish data QA for UAGC marketing program reports.

## Context
- Workspace root: ${ROOT}
- Outliers file (already loaded below): programs with missing names or suspicious program_id values before HTML report publish.
- Follow timezone and column rules from the sql-query skill excerpt.

## sql-query skill (excerpt)
${skillExcerpt}

## qa_outlier_programs.json
\`\`\`json
${outliersJson}
\`\`\`

## Tasks
1. Use the BigQuery MCP execute-query tool. Query \`advertising-data-mart.inquiries.vw_lead_extract_details\` with \`CURRENT_DATE('America/New_York')\` for date logic.
2. For each outlier row, verify whether lead counts and date ranges are plausible (e.g. null program_id bucket, Salesforce-style IDs, string IDs like "Sociology").
3. Write a concise markdown report to \`${REPORT_PATH}\` with:
   - Executive summary (pass / warn / fail)
   - Table: outlier key, BQ finding, recommendation
   - Suggested SQL snippets used (fenced)
4. Do not modify Python report generators or JSON source files unless a row is clearly a pipeline bug — then note the file to fix in prose only.

Keep the report under 80 lines. If BigQuery is unreachable, write the report explaining the blocker and exit with findings from the JSON only.`;
}

async function main(): Promise<void> {
  const apiKey = process.env.CURSOR_API_KEY?.trim();
  if (!apiKey) {
    console.error(
      "Missing CURSOR_API_KEY. Create one at https://cursor.com/dashboard/cloud-agents then:\n" +
        '  $env:CURSOR_API_KEY = "cursor_..."   # PowerShell\n' +
        "  npm run qa:outliers",
    );
    process.exit(1);
  }

  const [outliersRaw, skillRaw] = await Promise.all([
    readFile(OUTLIERS_PATH, "utf-8"),
    readFile(SKILL_PATH, "utf-8").catch(() => "(sql-query skill not found)"),
  ]);
  const skillExcerpt = skillRaw.slice(0, 4000);

  const agent = Agent.create({
    apiKey,
    model: { id: "composer-2" },
    local: {
      cwd: ROOT,
      settingSources: ["user"],
    },
    mcpServers,
  });

  try {
    const run = await agent.send(buildPrompt(outliersRaw, skillExcerpt));
    console.log(`[qa:outliers] agent=${agent.agentId} run=${run.id}`);

    for await (const event of run.stream()) {
      if (event.type === "status") {
        console.log(`[qa:outliers] status: ${event.status}`);
      }
      if (event.type === "tool_call" && event.status === "completed") {
        console.log(`[qa:outliers] tool: ${event.name}`);
      }
    }

    const result = await run.wait();
    if (result.status === "error") {
      console.error(`[qa:outliers] run ${result.id} ended with status=error`);
      process.exit(2);
    }

    await mkdir(path.dirname(REPORT_PATH), { recursive: true });
    try {
      const report = await readFile(REPORT_PATH, "utf-8");
      console.log("\n--- docs/sdk-qa-outliers.md ---\n");
      console.log(report);
    } catch {
      console.log(
        "[qa:outliers] finished; agent may have written the report — check docs/sdk-qa-outliers.md",
      );
      if (result.result) console.log(result.result);
    }

    console.log(`\n[qa:outliers] done in ${result.durationMs ?? "?"}ms`);
  } catch (err) {
    if (err instanceof CursorAgentError) {
      console.error(
        `[qa:outliers] startup failed: ${err.message} (retryable=${err.isRetryable})`,
      );
      process.exit(err.isRetryable ? 75 : 1);
    }
    throw err;
  } finally {
    await agent[Symbol.asyncDispose]();
  }
}

main();
