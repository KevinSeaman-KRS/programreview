"""Appendix HTML: data sources, formulas, and field mappings for the program report."""
from __future__ import annotations

import html
from datetime import date

from marketing_segment_hierarchy import (
    MARS_LEGACY_MAP,
    SEGMENT_ROLLUP_FALLBACK,
)
from report_periods import (
    MONTHLY_DETAIL_LABEL,
    PRIMARY_LABEL,
    PRIOR_LABEL,
)
from report_regions import REGION_ORDER, REGION_STATES
from report_agent_context import render_agent_build_section


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _mars_mapping_table() -> str:
    rows = []
    for legacy in sorted(MARS_LEGACY_MAP.keys()):
        m = MARS_LEGACY_MAP[legacy]
        rows.append(
            "<tr>"
            f"<td>{_esc(legacy)}</td>"
            f"<td>{_esc(m['marketing_rollup'])}</td>"
            f"<td>{_esc(m['segment_rollup'])}</td>"
            f"<td>{_esc(m['segment1'])}</td>"
            "</tr>"
        )
    body = "\n".join(rows)
    return (
        '<table class="methodology-table methodology-map-table">\n'
        "<thead><tr>"
        "<th>mars_segment_legacy</th>"
        "<th>Marketing rollup</th>"
        "<th>Segment rollup</th>"
        "<th>initial_marketing_segment1</th>"
        "</tr></thead>\n"
        f"<tbody>\n{body}\n</tbody></table>\n"
    )


def _rollup_fallback_table() -> str:
    rows = []
    for rollup in sorted(SEGMENT_ROLLUP_FALLBACK.keys()):
        m = SEGMENT_ROLLUP_FALLBACK[rollup]
        rows.append(
            "<tr>"
            f"<td><em>null legacy</em> + { _esc(rollup) }</td>"
            f"<td>{_esc(m['marketing_rollup'])}</td>"
            f"<td>{_esc(m['segment_rollup'])}</td>"
            f"<td>{_esc(m['segment1'])}</td>"
            "</tr>"
        )
    return (
        '<p class="methodology-note">When <code>mars_segment_legacy</code> is null, '
        "mapping uses BigQuery <code>marketing_segment_rollup</code>:</p>\n"
        '<table class="methodology-table methodology-map-table">\n'
        "<thead><tr>"
        "<th>Condition</th><th>Marketing rollup</th>"
        "<th>Segment rollup</th><th>segment1</th>"
        "</tr></thead>\n"
        f"<tbody>\n{''.join(rows)}\n</tbody></table>\n"
    )


def _region_mapping_list() -> str:
    parts = []
    for region in REGION_ORDER:
        states = ", ".join(sorted(REGION_STATES.get(region, frozenset())))
        parts.append(f"<li><strong>{_esc(region)}</strong>: { _esc(states) }</li>")
    return "<ul class=\"methodology-list\">" + "".join(parts) + "</ul>"


def render_methodology_appendix(report_date: date | None = None) -> str:
    """Two-page-style appendix: sources, formulas, then mappings."""
    when = (report_date or date.today()).strftime("%B %d, %Y")

    return f"""
    <div class="card methodology-block" id="methodology">
        <h2>Appendix: Methodology &amp; data dictionary</h2>
        <p class="methodology-intro">
            Reference for how metrics in this report are sourced, calculated, and labeled.
            Generated {when}. Pull scripts live in the project root; JSON artifacts feed
            <code>generate_full_report.py</code>.
        </p>

        <section class="methodology-page" id="methodology-sources">
            <h3>1. Data sources &amp; time windows</h3>

            <h4>BigQuery — lead funnel</h4>
            <dl class="methodology-dl">
                <dt>Project / dataset</dt>
                <dd><code>advertising-data-mart.inquiries</code></dd>
                <dt>Primary view</dt>
                <dd><code>vw_lead_extract_details</code> — one row per inquiry; program keyed on
                    <code>program_id</code> at inquiry time.</dd>
                <dt>Date field</dt>
                <dd><code>inquiry_date</code> (America/New_York calendar days; end dates exclusive).</dd>
                <dt>Primary window (matrix KPIs, widgets, Sankey)</dt>
                <dd>{_esc(PRIMARY_LABEL)} — script: <code>pull_full_data.py</code>,
                    <code>pull_program_detail_widgets.py</code>, <code>pull_sankey_flow.py</code></dd>
                <dt>Prior window (year-over-year comparison)</dt>
                <dd>{_esc(PRIOR_LABEL)} — same programs, prior 6 months in
                    <code>program_data_full.json</code> (<code>py_*</code> fields).</dd>
                <dt>Monthly detail (all program detail pages)</dt>
                <dd>{_esc(MONTHLY_DETAIL_LABEL)} — <code>program_data_full.json</code> →
                    <code>monthly</code> keyed by program.</dd>
                <dt>Program migration (all enrolling programs)</dt>
                <dd>Rolling 12 months from current date (NY) —
                    <code>pull_program_migration.py</code> → <code>program_migration.json</code>.</dd>
            </dl>

            <h4>SQL Server — enrolled students &amp; program bridge</h4>
            <dl class="methodology-dl">
                <dt>Demographics</dt>
                <dd><code>dbo.StudentRevenueMaster</code> matriculations in the
                    12-month demographics window (<code>DEMOGRAPHICS_MATRIC_*</code> in
                    <code>report_periods.py</code>), joined via <code>dbo.program_srm_bridge</code>.
                    % Pell among Core LOB; % military funding among Military LOB; transfer credits undergraduate only; dependents excluded.</dd>
                <dt>Enrollment line of business (widgets)</dt>
                <dd>Same SRM matric window; LOB from <code>lineofbusiness</code> on enrolled students.</dd>
                <dt>Account group (matrix column)</dt>
                <dd><code>account_group</code> from bridge table / <code>data/program_srm_bridge.json</code>
                    (built with <code>scripts/build_program_bridge.py</code> from
                    <code>dbo.vw_program</code>).</dd>
            </dl>

            <h4>Artifact files consumed by the HTML report</h4>
            <ul class="methodology-list">
                <li><code>program_data_full.json</code> — matrix totals, prior period, monthly series</li>
                <li><code>program_detail_widgets.json</code> — marketing mix, Paid segment1 breakdown, enrollment LOB</li>
                <li><code>program_sankey_flow.json</code> — segment1 inflow + funnel stages</li>
                <li><code>program_demographics.json</code> — SRM profile + US regions + degree-level baselines</li>
                <li><code>program_migration.json</code> — inquiry ↔ applied program flows (enrolling programs)</li>
                <li><code>data/program_srm_bridge.json</code> — program metadata and account groups</li>
                <li><code>data/program_alignment.json</code> — college, division, department, and academic
                    leadership by program (from <em>Program Alignment List</em> workbook;
                    <code>scripts/build_program_alignment.py</code>)</li>
            </ul>
        </section>

        <section class="methodology-page" id="methodology-formulas">
            <h3>2. Metrics &amp; formulas</h3>

            <h4>Lead funnel flags (BigQuery)</h4>
            <ul class="methodology-list">
                <li><strong>Leads</strong> — <code>COUNT(*)</code> inquiries in window.</li>
                <li><strong>Apps Started</strong> — <code>SUM(is_app_started)</code>.</li>
                <li><strong>Submitted</strong> — <code>SUM(is_app_submitted)</code> (monthly table only).</li>
                <li><strong>Decisions</strong> — <code>SUM(is_appin)</code> (application-in / decision stage).</li>
                <li><strong>Final enrollments</strong> — <code>SUM(is_new_enrollment_final)</code>;
                    used for matrix Enrl, Sankey funnel, and navigational %.</li>
            </ul>

            <h4>Summary matrix</h4>
            <ul class="methodology-list">
                <li><strong>Prior % change</strong> — <code>(current − prior) / prior × 100</code>;
                    shown as ▲/▼/► when change exceeds ±5%; “NEW” if prior is zero.</li>
                <li><strong>% Core</strong> — share of final enrollments with LOB label
                    <em>Core</em> (widget/SRM LOB buckets).</li>
                <li><strong>% Military</strong> — SRM <code>lineofbusiness</code> = Military when demographics exist;
                    else widget LOB bucket <em>Military</em>.</li>
                <li><strong>% B2B</strong> — FTG + TB: SRM <em>Full Tuition Grant</em> +
                    <em>Tuition Benefit</em> (displayed FTG / TB); else same labels in widget LOB.</li>
                <li><strong>% Navig</strong> — <code>navigational_enrollments ÷ new_enrollments × 100</code>
                    (enrollment mix, not lead mix). Navigational paths: legacy values mapped to
                    marketing rollup Navigational, or null legacy with rollup
                    Brand - Search / Organic.</li>
                <li><strong>Med Age / % Female</strong> — median <code>age_at_matric</code> and female % from SRM
                    (male/female only, renormalized).</li>
                <li><strong>Net migration</strong> — enrollment view:
                    inflow to this applied program minus outflow to other programs
                    (12-month window on program detail pages).</li>
                <li><strong>Sort order</strong> — <code>new_enrollments</code> descending; level total row first,
                    undecided rollup last (undergraduate tab).</li>
                <li><strong>Green highlight (top 5)</strong> — per tab, five highest values among enrolling programs
                    for % Core, % Military, and % B2B (Undecided rollup excluded from ranking).</li>
            </ul>

            <h4>Detail widgets &amp; charts</h4>
            <ul class="methodology-list">
                <li><strong>Leads — marketing rollup</strong> — inquiry counts by Paid / Navigational / B2B
                    (<code>resolve_marketing_levels</code>).</li>
                <li><strong>Enrollments — marketing rollup</strong> — same hierarchy on rows with
                    <code>is_new_enrollment_final = 1</code>.</li>
                <li><strong>Paid details</strong> — Paid-only leads and enrollments broken out by
                    <code>initial_marketing_segment1</code> (segment1).</li>
                <li><strong>Sankey inflow</strong> — segment1 on primary-window inquiries;
                    funnel stages from <code>program_data_full.json</code> funnel block.</li>
                <li><strong>Monthly Enroll %</strong> — <code>new_enrollments ÷ leads</code> per month;
                    App Start % and Decision % use the same lead denominator.</li>
                <li><strong>4-month rolling average</strong> — mean of leads for months <em>i−3…i</em>;
                    plotted from month 4 onward.</li>
                <li><strong>Geography index</strong> — <code>round(program_region_% ÷ baseline_region_% × 100)</code>;
                    baseline = all enrolled students at same degree level (Undergrad or Grad).</li>
                <li><strong>Demographic “index” callouts</strong> — plain-language point difference vs baseline
                    (e.g. “5 pts above”), not the regional index formula.</li>
            </ul>

            <h4>LOB display labels (report UI)</h4>
            <table class="methodology-table">
                <thead><tr><th>SRM / widget label</th><th>Shown as</th></tr></thead>
                <tbody>
                    <tr><td>Core</td><td>Core</td></tr>
                    <tr><td>Full Tuition Grant</td><td>FTG</td></tr>
                    <tr><td>Tuition Benefit</td><td>TB</td></tr>
                    <tr><td>Military</td><td>Military</td></tr>
                </tbody>
            </table>
        </section>

        <section class="methodology-page" id="methodology-mappings">
            <h3>3. Marketing segment mappings</h3>
            <p class="methodology-note">
                Source field: <code>mars_segment_legacy</code> (≈ initial marketing segment on the inquiry).
                Hierarchy columns match business rollup used in widgets and Sankey.
                Unmapped legacy + rollup combinations are excluded from segment charts.
            </p>
            {_mars_mapping_table()}
            {_rollup_fallback_table()}
        </section>

        <section class="methodology-page" id="methodology-regions">
            <h3>4. US region mapping (enrollment geography)</h3>
            <p class="methodology-note">
                Student <code>state</code> from SRM → USPS abbreviation → region bucket.
                Map sketch shows % of program enrollments per region; callout
                <strong>index</strong> uses the formula in section 2.
            </p>
            {_region_mapping_list()}
        </section>

        {render_agent_build_section()}
    </div>
"""
