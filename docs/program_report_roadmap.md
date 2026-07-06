# Program Report - Next Iteration Roadmap

## Data Window

- **YoY Jul–Jun windows** (implemented): Primary Jul 2025 – Jun 2026 vs Prior Jul 2024 – Jun 2025
- **Monthly detail:** 15 months (Apr 2025 – Jun 2026)
- **SRM matric** aligned to primary window; migration uses primary year only
- **Mix YoY tab:** portfolio degree-level + LOB enrollment mix (see `pull_portfolio_mix_yoy.py`)
- **Standalone insights:** `generate_program_insights.py` → `deploy/program-insights.html` (mix analysis + program movers; not on detail profiles)

## Matrix Improvements

1. **Separate tabs by level**: Split into Graduate and Undergraduate (two separate sections/tabs)
2. **Hyperlinks per row**:
   - Link to detail page (with screenshots)
   - Link to live program page on uagc.edu
3. **Dual screenshots**: Capture both desktop and mobile versions
   - Desktop: standard 1280px viewport
   - Mobile: narrow viewport (~390px), scroll down to capture more content (not just above-the-fold)
   - Mobile is a large share of traffic — important to see that experience

## Detail Page Enhancements

### KPI Scorecards
- Leads, App Starts, Decisions, Enrollments boxes should include:
  - Current period value
  - **% change vs. prior year** (same period last year)
  - Up/down icon to indicate direction
- This gives immediate context on whether a program is growing or shrinking

### Monthly Trend Chart
- Flip the "Lead Volume (Monthly)" visualization to **horizontal time axis** (months across the x-axis, volume on y-axis)
- Standard bar or line chart orientation

### Sankey / Flow Diagram — implemented (marketing inflow)
- D3 Sankey: `marketing_segment_rollup` → Inquiries (merge) → funnel stages + drop-offs
- Data: `pull_sankey_flow.py` → `program_sankey_flow.json`
- **Detail widgets:** segment stacked bars + LOB bar (`pull_program_detail_widgets.py`)
- **Prose summary** on detail pages (`report_prose_summary.py`)
- **Matrix:** Undecided rolled into one row at bottom of undergrad tab; `% Core`, `% Nav`, `Net`, `Net Enrl%` on the right
- **Enrollments:** `is_new_enrollment_final` throughout `pull_full_data.py`

- **Marketing inflow (reference):** `marketing_segment_rollup` flows into Inquiries before the funnel
  - Layout: `[Segment 1..N] → Inquiries (merge) → App Starts / drop → … → Enrollments`
  - Shows where volume enters before conversion losses
  - Data: group by `marketing_segment_rollup` + funnel flags on same inquiry rows
  - Current rollup values (~12 mo, all programs): Organic, Display, Affiliate, Affiliate - Search, Non Brand - Search, Brand - Search (+ small NULL bucket)
  - May need grouping rules if 6+ segments feel too busy (e.g., collapse search variants)
  - Downstream funnel stays aggregate after merge (segment mix at entry; not parallel paths through entire funnel unless requested later)
- **Future enhancement**: Add `is_first_contacted` between Inquiry and App Start
  - This splits the biggest drop-off into "never contacted" vs "contacted but didn't start app"
  - Requires data quality review first — contact data may need cleanup
  - Much more actionable for EA management
- Per-program dropdown to switch views
- Library: d3-sankey v0.12

### Inquiry vs. Applied Program Migration (detail tab)

Program-owner view: **two flow blocks** (do not conflate metrics).

### Block A — Program enrollments (`enrollment_view`)

Anchor = **applied program**. Count **`is_new_enrollment_final = 1`** only.

**Summary strip:** final enrollments in program, same-path, gained, lost, net (+18 for BA SCJ example).

| Inquiry program | Final enrollments | % | Applied (enrolled) program |

Row order: same-path → inflows (“Into this program”) → outflows (“Enrolled in a different program”). Matrix **Net / Net %** uses this view.

### Block B — Inquiry cohort (`lead_cohort_view`)

Anchor = **inquiry program**. Denominator = **12-month inquiry leads** on `program_id`.

**Summary strip:** inquiry leads, final enrollments, **enrollment_rate_pct**, in-program vs elsewhere.

Same 4-column table; % = share of final enrollments from this inquiry cohort.

**Rules (both):** `is_new_enrollment_final`, same `degree_level` = `applied_degree_level`, exclude cross-level; `Undecided%` → `Undecided` on inquiry side only; `applied_program_id` required for enrollee rows in block A.

No Sankey/chord on detail tab for v1.

## Student Demographic Profile (Detail Page) — implemented

- Source: `dbo.StudentRevenueMaster` (enrolled students, 12-mo matric window)
- Join: `dbo.program_srm_bridge` → `program_id`
- Pull: `pull_program_demographics.py` → `program_demographics.json`
- Report block: **Enrolled student profile** on each detail page (after program flow, before funnel)
- Fields: gender, race, Pell, line of business, age buckets, marital status, top states (≥3%)
- Index badges: Female / Minority vs same degree-level baseline (`idx` = program % ÷ baseline % × 100)
- **Future: indexed comparisons, not raw share alone**
  - Raw % (e.g., CA/TX/FL) often mirrors US population — less interesting for commentary
  - Compare each program to a **baseline** and highlight **over/under-index**:
    - Program vs. **all enrolled students**
    - Program vs. **same degree level** (MBA vs all graduate; BA Psychology vs all undergraduate)
    - Optionally vs. **all leads** at same level (enrolled profile vs inquiry pool — selection effect)
  - Display: index = (program % / baseline %) × 100; call out dimensions where index ≠ 100 (e.g., "Female +12 pts vs undergrad avg")
  - Geography: consider state **per-capita** or index vs national/state enrollment baseline, not top states by volume alone
  - **State focus rules (user preference):**
    - Prioritize **regional patterns** (e.g., Southwest, Southeast) or **high-volume states** where n is meaningful
    - Ignore or de-emphasize over-index in **small states** (e.g., WV, WY) — low volume rarely drives strategic action
    - Only surface state-level callouts when enrollment volume supports it

## Technical Notes

- Applied program fields in BigQuery: `applied_program_id`, `applied_degree_level`, `applied_degree_type`, `applied_program_name`, `applied_program_code`, `applied_area_of_interest`
- Inquiry program fields: `program_id`, `degree_level`, `degree_type`, `program_name`, `program_code`
- Mobile screenshots: use Playwright with `viewport: {width: 390, height: 844}` and `fullPage: true` or scroll-and-stitch
- Sankey: consider embedding via D3.js in the HTML report, or using a Python lib like plotly
