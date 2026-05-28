"""Agent / Cursor build context for methodology appendix."""
from __future__ import annotations

import html
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Project skills (`.cursor/skills/`) used while building this report.
PROJECT_SKILLS: list[dict[str, str]] = [
    {
        "name": "sql-query",
        "role": "Primary",
        "summary": (
            "BigQuery and SQL Server patterns for lead funnel, program metrics, "
            "and enrollment pulls (<code>vw_lead_extract_details</code>, SRM)."
        ),
    },
    {
        "name": "uagc-brand",
        "role": "Primary",
        "summary": (
            "Official UAGC colors, typography (Montserrat), and editorial rules "
            "applied to report CSS and chart ramps."
        ),
    },
    {
        "name": "ui-ux-pro-max",
        "role": "Reference",
        "summary": (
            "Design-system lookup (styles, palettes, chart guidance); stub in repo "
            "pending full package from team."
        ),
    },
]

# MCP servers used or available during report development.
MCP_SERVERS: list[dict[str, str]] = [
    {
        "name": "user-bigquery",
        "role": "Primary data",
        "tools": "execute-query, list-tables, describe-table",
        "use": "Lead funnel, Sankey segment mix, marketing widgets, matrix pulls.",
    },
    {
        "name": "user-mssql",
        "role": "Primary data",
        "tools": "execute_sql",
        "use": "StudentRevenueMaster demographics, LOB, program bridge (CVue codes).",
    },
    {
        "name": "user-git",
        "role": "Deploy",
        "tools": "status, diff, commit, log, branch",
        "use": "GitHub Pages deploy repo (<code>uagc-program-report</code>).",
    },
    {
        "name": "user-fetch",
        "role": "Supporting",
        "tools": "fetch",
        "use": "Landing-page checks and live URL validation.",
    },
    {
        "name": "user-filesystem",
        "role": "Supporting",
        "tools": "read/write file, list directory",
        "use": "Artifact and report file management.",
    },
    {
        "name": "user-memory",
        "role": "Supporting",
        "tools": "knowledge graph",
        "use": "Workspace facts and preferences across sessions.",
    },
    {
        "name": "user-sequential-thinking",
        "role": "Supporting",
        "tools": "sequentialthinking",
        "use": "Structured reasoning on complex pipeline changes.",
    },
    {
        "name": "user-time",
        "role": "Supporting",
        "tools": "get_current_time, convert_time",
        "use": "Period labels and timezone alignment (America/New_York).",
    },
    {
        "name": "user-google-ads-mcp",
        "role": "Available",
        "tools": "search, list_accessible_customers",
        "use": "Not required for this static report; enabled in workspace.",
    },
    {
        "name": "plugin-slack-slack",
        "role": "Available",
        "tools": "Slack integration",
        "use": "Not used in report generation.",
    },
]


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def load_cursor_usage_stats() -> dict | None:
    """Load usage summary from Cursor dashboard export CSV if present."""
    script = ROOT / "scripts" / "analyze_cursor_usage.py"
    if not script.exists():
        return None
    spec = importlib.util.spec_from_file_location("analyze_cursor_usage", script)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.analyze_usage()


def render_agent_build_section() -> str:
    """Section 5: Cursor Agent, skills, MCP, and usage summary."""
    usage = load_cursor_usage_stats()

    skills_rows = "".join(
        "<tr>"
        f"<td><code>{_esc(s['name'])}</code></td>"
        f"<td>{_esc(s['role'])}</td>"
        f"<td>{s['summary']}</td>"
        "</tr>"
        for s in PROJECT_SKILLS
    )

    mcp_rows = "".join(
        "<tr>"
        f"<td><code>{_esc(m['name'])}</code></td>"
        f"<td>{_esc(m['role'])}</td>"
        f"<td>{_esc(m['tools'])}</td>"
        f"<td>{_esc(m['use'])}</td>"
        "</tr>"
        for m in MCP_SERVERS
    )

    usage_html = ""
    if usage:
        phase_rows = ""
        total = usage["total_tokens"]
        for phase in usage["phases"]:
            pct = 100 * phase["tokens"] / total if total else 0
            phase_rows += (
                "<tr>"
                f"<td>{_esc(phase['label'])}</td>"
                f"<td>{_fmt_tokens(phase['tokens'])}</td>"
                f"<td>{pct:.0f}%</td>"
                f"<td>{phase['hours']}</td>"
                f"<td>{phase['sessions']}</td>"
                "</tr>"
            )
        model_items = ", ".join(
            f"{_esc(name)} ({_fmt_tokens(tok)})" for name, tok in usage.get("models", [])
        )
        usage_html = f"""
            <h4>Token &amp; time summary</h4>
            <p class="methodology-note">
                Pulled from Cursor usage export <code>{_esc(usage['csv_file'])}</code>
                ({_esc(usage['date_range'])}, UTC). Figures are <strong>agent events only</strong>
                (not IDE autocomplete). Refresh by exporting from the
                <a href="https://cursor.com/dashboard?tab=usage" target="_blank" rel="noopener">
                Cursor usage dashboard</a> and saving as
                <code>data/cursor_usage_events.csv</code> or updating the file in Downloads.
            </p>
            <table class="methodology-table">
            <thead><tr><th>Metric</th><th>Value</th></tr></thead>
            <tbody>
            <tr><td>Agent events</td><td>{usage['events']:,}</td></tr>
            <tr><td>Total tokens</td><td>{usage['total_tokens']:,} ({_fmt_tokens(usage['total_tokens'])})</td></tr>
            <tr><td>Agent sessions</td><td>{usage['sessions']} (gap &gt; 45 min)</td></tr>
            <tr><td>Estimated active time</td><td><strong>{usage['active_hours_est']} hours</strong>
                (session span {usage['session_span_hours']}h + padding)</td></tr>
            </tbody></table>
            <table class="methodology-table">
            <thead><tr><th>Work phase</th><th>Tokens</th><th>%</th><th>Est. hours</th><th>Sessions</th></tr></thead>
            <tbody>{phase_rows}</tbody></table>
            <p class="methodology-note">{_esc(usage['methodology_note'])}</p>
            <p class="methodology-note"><strong>Models (by token volume):</strong> {model_items or '—'}</p>
        """
    else:
        usage_html = """
            <h4>Token &amp; time summary</h4>
            <p class="methodology-note">
                No Cursor usage CSV found. Export from the
                <a href="https://cursor.com/dashboard?tab=usage" target="_blank" rel="noopener">
                usage dashboard</a> and save as <code>data/cursor_usage_events.csv</code>, then
                regenerate the report (<code>python generate_full_report.py</code>).
            </p>
        """

    return f"""
        <section class="methodology-page" id="methodology-agent">
            <h3>5. Cursor Agent build context</h3>
            <p class="methodology-note">
                This report was built iteratively in <strong>Cursor</strong> using the
                <strong>Agent</strong> (Composer) with project rules in <code>AGENTS.md</code>,
                workspace rules under <code>.cursor/rules/</code>, and Python pull/generate scripts
                in the repo root. The HTML is static output from
                <code>generate_full_report.py</code>; data refreshes via BigQuery/SQL pull scripts.
            </p>

            <h4>Agent skills (project)</h4>
            <table class="methodology-table">
            <thead><tr><th>Skill</th><th>Role</th><th>How it was used</th></tr></thead>
            <tbody>{skills_rows}</tbody></table>
            <p class="methodology-note">
                Additional global Cursor skills (SDK, create-rule, canvas, code-review, etc.) are
                installed in the IDE but were secondary to the project skills above for this deliverable.
            </p>

            <h4>MCP servers</h4>
            <table class="methodology-table methodology-map-table">
            <thead><tr><th>Server</th><th>Role</th><th>Tools</th><th>Use in this report</th></tr></thead>
            <tbody>{mcp_rows}</tbody></table>

            {usage_html}
        </section>
    """
