"""HTML render helpers for program detail sections (Sankey, state/region, matrix)."""
from __future__ import annotations

import json
from collections import defaultdict

from marketing_segment_hierarchy import (
    MARKETING_ROLLUP_ORDER,
    SEGMENT1_ORDER,
    SEGMENT1_TO_MARKETING_ROLLUP,
)
from report_demographics import display_lineofbusiness, pct_from_dist
from report_us_region_map import render_us_region_map_html


def is_undecided_program(program: dict) -> bool:
    return (program.get("program_name") or "").startswith("Undecided")


def change_icon_prior(pct: float | None) -> str:
    if pct is None:
        return '<span class="chg-prior chg-new">NEW</span>'
    if pct > 5:
        return f'<span class="chg-prior chg-up">&#9650; {pct:+.0f}%</span>'
    if pct < -5:
        return f'<span class="chg-prior chg-down">&#9660; {pct:+.0f}%</span>'
    return f'<span class="chg-prior chg-flat">&#9654; {pct:+.0f}%</span>'


def pct_core_from_widgets(
    detail_widgets: dict, pid: str, program: dict | None = None
) -> float | None:
    if program and program.get("_pct_core_weighted") is not None:
        return program["_pct_core_weighted"]
    for bucket in detail_widgets.get(pid, {}).get("enrollment_lob", {}).get("buckets", []):
        if bucket.get("label") == "Core":
            return bucket.get("pct")
    return None


UNDERGRAD_TOTAL_ID = "UNDERGRAD_TOTAL"
GRADUATE_TOTAL_ID = "GRADUATE_TOTAL"
OVERALL_TOTAL_ID = "OVERALL_TOTAL"
UNDECIDED_ROLLUP_ID = "UNDECIDED_ROLLUP"

LEVEL_DETAIL_URLS: dict[str, str] = {
    UNDERGRAD_TOTAL_ID: "https://www.uagc.edu/online-degrees/bachelors",
    GRADUATE_TOTAL_ID: "https://www.uagc.edu/online-degrees/masters",
}

UNDECIDED_DETAIL_LABEL = "Undecided inquiry placeholders"

LEVEL_DETAIL_LABELS: dict[str, str] = {
    UNDERGRAD_TOTAL_ID: "Total undergraduate",
    GRADUATE_TOTAL_ID: "Total graduate",
    UNDECIDED_ROLLUP_ID: UNDECIDED_DETAIL_LABEL,
}

LEVEL_DETAIL_URLS[UNDECIDED_ROLLUP_ID] = "https://www.uagc.edu/online-degrees"

LEVEL_DETAIL_PROGRAM_IDS = frozenset(LEVEL_DETAIL_URLS.keys())

MATRIX_ROLLUP_IDS = frozenset({
    UNDERGRAD_TOTAL_ID,
    GRADUATE_TOTAL_ID,
    OVERALL_TOTAL_ID,
    UNDECIDED_ROLLUP_ID,
})


def aggregate_matrix_programs(
    programs: list[dict],
    *,
    program_id: str,
    program_name: str,
    account_group: str,
    degree_level: str,
    degree_type: str = "",
) -> dict:
    """Sum funnel metrics and enrollment-weighted % Nav across a program list."""
    if not programs:
        return {}
    agg: dict = {
        "program_id": program_id,
        "program_name": program_name,
        "account_group": account_group,
        "degree_level": degree_level,
        "degree_type": degree_type,
        "leads": 0,
        "apps_started": 0,
        "apps_submitted": 0,
        "decisions": 0,
        "new_enrollments": 0,
        "py_leads": 0,
        "py_apps_started": 0,
        "py_apps_submitted": 0,
        "py_decisions": 0,
        "py_new_enrollments": 0,
        "navigational_enrollments": 0,
    }
    for p in programs:
        for key in (
            "leads",
            "apps_started",
            "apps_submitted",
            "decisions",
            "new_enrollments",
            "py_leads",
            "py_apps_started",
            "py_apps_submitted",
            "py_decisions",
            "py_new_enrollments",
        ):
            agg[key] += p.get(key, 0) or 0
        enr = p.get("new_enrollments") or 0
        if enr and p.get("pct_navigational") is not None:
            agg["navigational_enrollments"] += int(
                enr * p["pct_navigational"] / 100
            )
    if agg["new_enrollments"]:
        agg["pct_navigational"] = round(
            agg["navigational_enrollments"] / agg["new_enrollments"] * 100, 1
        )
    else:
        agg["pct_navigational"] = None
    return agg


def enrich_matrix_rollup_row(
    agg: dict,
    program_ids: list[str],
    detail_widgets: dict,
    demographics: dict,
    migration: dict | None = None,
    enrollment_view_fn=None,
) -> None:
    """Attach LOB, demographic, and net-migration rollups for matrix summary rows."""
    core_n, mil_n, b2b_n, enr_n = rollup_lob_gross_counts(detail_widgets, program_ids)
    agg["_rollup_core_enrolls"] = core_n
    agg["_rollup_military_enrolls"] = mil_n
    agg["_rollup_b2b_enrolls"] = b2b_n
    if enr_n:
        agg["_pct_core_weighted"] = round(core_n / enr_n * 100, 1)
    med, fem = rollup_demographics(demographics, program_ids)
    if med is not None:
        agg["_rollup_median_age"] = med
    if fem is not None:
        agg["_rollup_female_pct"] = fem
    agg["_rollup_military_pct"] = rollup_lob_pct(
        detail_widgets, program_ids, ("Military",)
    )
    agg["_rollup_b2b_pct"] = rollup_lob_pct(
        detail_widgets,
        program_ids,
        ("Full Tuition Grant", "Tuition Benefit"),
    )
    if migration and enrollment_view_fn:
        mig = rollup_net_migration(migration, program_ids, enrollment_view_fn)
        if mig:
            agg["_synthetic_migration"] = mig


def rollup_net_migration(
    migration: dict,
    program_ids: list[str],
    enrollment_view_fn,
) -> dict | None:
    """Synthetic migration payload for a matrix total row (sum of net in/out)."""
    net_sum = 0
    enr_in_sum = 0
    any_data = False
    for pid in program_ids:
        ev = enrollment_view_fn(migration.get(pid))
        if not ev or not ev.get("enrollments_in"):
            continue
        any_data = True
        net_sum += ev.get("net_migration", 0) or 0
        enr_in_sum += ev.get("enrollments_in", 0) or 0
    if not any_data:
        return None
    return {
        "enrollment_view": {
            "enrollments_in": enr_in_sum,
            "net_migration": net_sum,
            "net_pct_enrollments": (
                round(100 * net_sum / enr_in_sum, 1) if enr_in_sum else None
            ),
        }
    }


def aggregate_undecided_programs(programs: list[dict]) -> dict:
    """Roll up metrics for all Undecided inquiry programs."""
    return aggregate_matrix_programs(
        programs,
        program_id=UNDECIDED_ROLLUP_ID,
        program_name="Undecided (all inquiry placeholders)",
        account_group="Undecided",
        degree_level="Undergraduate",
        degree_type="Undecided",
    )


def fmt_matrix_pct(pct: float | None, decimals: int = 0) -> str:
    if pct is None:
        return "—"
    if decimals <= 0:
        return f"{round(pct):.0f}%"
    return f"{pct:.{decimals}f}%"


def fmt_matrix_count(count: int | None) -> str:
    if count is None or count <= 0:
        return "—"
    return f"{count:,}"


CORE_LOB_LABELS = ("Core",)
MILITARY_LOB_LABELS = ("Military",)
B2B_LOB_LABELS = ("Full Tuition Grant", "Tuition Benefit")


def lob_enroll_count_from_widgets(
    detail_widgets: dict,
    pid: str,
    labels: tuple[str, ...],
) -> int:
    lob = detail_widgets.get(pid, {}).get("enrollment_lob", {})
    return sum(
        int(b.get("count", 0))
        for b in lob.get("buckets", [])
        if b.get("label") in labels
    )


def lob_enroll_count_from_demographics(
    prof: dict | None,
    labels: tuple[str, ...],
) -> int:
    if not prof or not prof.get("count"):
        return 0
    total = int(prof["count"])
    lob = prof.get("lineofbusiness", {}) or {}
    return sum(round(total * (lob.get(label, 0) or 0) / 100) for label in labels)


def matrix_lob_enroll_count(
    detail_widgets: dict,
    demographics: dict,
    pid: str,
    labels: tuple[str, ...],
    program: dict | None = None,
    *,
    rollup_count_key: str | None = None,
) -> int | None:
    """Gross matriculated enrollments for LOB bucket(s); prefers widget counts."""
    if program and rollup_count_key and program.get(rollup_count_key) is not None:
        return int(program[rollup_count_key])
    n = lob_enroll_count_from_widgets(detail_widgets, pid, labels)
    if n > 0:
        return n
    prof = demographics.get(pid)
    d = lob_enroll_count_from_demographics(prof, labels)
    return d if d > 0 else None


def rollup_lob_gross_counts(
    detail_widgets: dict,
    program_ids: list[str],
) -> tuple[int, int, int, int]:
    """Sum Core, Military, B2B (FTG+TB), and total LOB enrollments across programs."""
    core_n = mil_n = b2b_n = enr_n = 0
    for pid in program_ids:
        lob = detail_widgets.get(pid, {}).get("enrollment_lob", {})
        enr_n += int(lob.get("total", 0) or 0)
        for b in lob.get("buckets", []):
            label = b.get("label")
            c = int(b.get("count", 0) or 0)
            if label == "Core":
                core_n += c
            elif label == "Military":
                mil_n += c
            elif label in B2B_LOB_LABELS:
                b2b_n += c
    return core_n, mil_n, b2b_n, enr_n


def lob_pct_from_widgets(
    detail_widgets: dict,
    pid: str,
    labels: tuple[str, ...],
) -> float | None:
    lob = detail_widgets.get(pid, {}).get("enrollment_lob", {})
    total = lob.get("total", 0)
    if not total:
        return None
    n = sum(
        b["count"]
        for b in lob.get("buckets", [])
        if b.get("label") in labels
    )
    return round(n / total * 100, 1) if total else None


def rollup_lob_pct(
    detail_widgets: dict,
    program_ids: list[str],
    labels: tuple[str, ...],
) -> float | None:
    total_enr = 0
    label_n = 0
    for pid in program_ids:
        lob = detail_widgets.get(pid, {}).get("enrollment_lob", {})
        t = lob.get("total", 0)
        if not t:
            continue
        total_enr += t
        for b in lob.get("buckets", []):
            if b.get("label") in labels:
                label_n += int(b["count"])
    return round(label_n / total_enr * 100, 1) if total_enr else None


def matrix_military_b2b_pct(
    demographics: dict,
    detail_widgets: dict,
    pid: str,
    program: dict | None = None,
) -> tuple[float | None, float | None]:
    if program:
        if program.get("_rollup_military_pct") is not None:
            mil = program["_rollup_military_pct"]
        else:
            mil = None
        if program.get("_rollup_b2b_pct") is not None:
            b2b = program["_rollup_b2b_pct"]
        else:
            b2b = None
        if mil is not None or b2b is not None:
            return mil, b2b

    prof = demographics.get(pid)
    if prof and prof.get("count"):
        lob = display_lineofbusiness(prof.get("lineofbusiness", {}))
        mil = lob.get("Military")
        b2b = (lob.get("FTG") or 0) + (lob.get("TB") or 0)
        return (
            mil if mil is not None else None,
            b2b if b2b else None,
        )

    mil = lob_pct_from_widgets(detail_widgets, pid, ("Military",))
    b2b = lob_pct_from_widgets(
        detail_widgets, pid, ("Full Tuition Grant", "Tuition Benefit")
    )
    return mil, b2b


def matrix_top_n_program_ids(
    row_metrics: list[dict],
    field: str,
    n: int = 5,
) -> set[str]:
    """Top N programs by numeric field (e.g. gross LOB enroll counts)."""
    scored = [
        (r["program_id"], r[field])
        for r in row_metrics
        if r.get(field) is not None
        and r[field] > 0
        and r["program_id"] not in MATRIX_ROLLUP_IDS
    ]
    scored.sort(key=lambda x: -x[1])
    return {pid for pid, _ in scored[:n]}


def matrix_age_female(
    demographics: dict,
    pid: str,
    program: dict | None = None,
) -> tuple[str, str]:
    if program:
        if program.get("_rollup_median_age") is not None:
            med = program["_rollup_median_age"]
        else:
            med = None
        if program.get("_rollup_female_pct") is not None:
            fem = program["_rollup_female_pct"]
            return (
                str(int(med)) if med is not None else "—",
                fmt_matrix_pct(fem),
            )
    prof = demographics.get(pid)
    if not prof or not prof.get("count"):
        return "—", "—"
    female = pct_from_dist(prof.get("gender", {}), "Female")
    med = prof.get("age_median")
    return (
        str(med) if med is not None else "—",
        fmt_matrix_pct(female),
    )


def _pct_distribution(
    counts: dict[str, int], order: list[str]
) -> tuple[list[dict], int]:
    filtered = {k: v for k, v in counts.items() if v > 0}
    total = sum(filtered.values())
    if total == 0:
        return [], 0
    rows = []
    for key in order:
        c = filtered.get(key, 0)
        if c:
            rows.append({"label": key, "count": c, "pct": round(c / total * 100, 1)})
    for key, c in sorted(filtered.items()):
        if key not in order:
            rows.append({"label": key, "count": c, "pct": round(c / total * 100, 1)})
    return rows, total


def _sum_widget_bucket_rows(rows: list[dict], dest: dict[str, int]) -> None:
    for row in rows:
        label = row.get("label")
        if label:
            dest[label] += int(row.get("count") or 0)


LOB_WIDGET_ORDER = ["Core", "Full Tuition Grant", "Tuition Benefit", "Military"]


def rollup_detail_widgets(detail_widgets: dict, program_ids: list[str]) -> dict:
    """Synthetic per-level widget payload (sum counts, then %)."""
    rollup_leads: dict[str, int] = defaultdict(int)
    rollup_enr: dict[str, int] = defaultdict(int)
    paid_leads: dict[str, int] = defaultdict(int)
    paid_enr: dict[str, int] = defaultdict(int)
    lob_raw: dict[str, int] = defaultdict(int)

    for pid in program_ids:
        w = detail_widgets.get(pid) or {}
        seg = w.get("marketing_segment") or {}
        _sum_widget_bucket_rows(seg.get("rollup_leads") or [], rollup_leads)
        _sum_widget_bucket_rows(seg.get("rollup_enrollments") or [], rollup_enr)
        _sum_widget_bucket_rows(seg.get("paid_leads_breakdown") or [], paid_leads)
        _sum_widget_bucket_rows(seg.get("paid_enrollment_breakdown") or [], paid_enr)
        lob = w.get("enrollment_lob") or {}
        _sum_widget_bucket_rows(lob.get("buckets") or [], lob_raw)

    rl_rows, rl_total = _pct_distribution(dict(rollup_leads), MARKETING_ROLLUP_ORDER)
    re_rows, re_total = _pct_distribution(dict(rollup_enr), MARKETING_ROLLUP_ORDER)
    pl_rows, pl_total = _pct_distribution(dict(paid_leads), list(paid_leads.keys()))
    pe_rows, pe_total = _pct_distribution(dict(paid_enr), list(paid_enr.keys()))
    lob_rows, lob_total = _pct_distribution(dict(lob_raw), LOB_WIDGET_ORDER)

    return {
        "marketing_segment": {
            "rollup_leads": rl_rows,
            "rollup_leads_total": rl_total,
            "rollup_enrollments": re_rows,
            "rollup_enrollments_total": re_total,
            "paid_leads_breakdown": pl_rows,
            "paid_leads_total": pl_total,
            "paid_enrollment_breakdown": pe_rows,
            "paid_enrollments_total": pe_total,
        },
        "enrollment_lob": {"buckets": lob_rows, "total": lob_total},
    }


def _merge_weighted_distributions(
    profiles: list[tuple[dict[str, float], int]],
) -> dict[str, float]:
    buckets: dict[str, float] = defaultdict(float)
    total = 0
    for dist, n in profiles:
        if not dist or n <= 0:
            continue
        for key, pct in dist.items():
            buckets[key] += n * pct / 100.0
        total += n
    if total <= 0:
        return {}
    return {k: round(v / total * 100, 1) for k, v in buckets.items() if v > 0}


def rollup_demographics_profile(
    demographics: dict,
    program_ids: list[str],
    *,
    label: str,
) -> dict | None:
    """Enrollment-weighted demographic profile for level-total detail pages."""
    profiles = []
    for pid in program_ids:
        prof = demographics.get(pid)
        if prof and prof.get("count"):
            profiles.append(prof)
    if not profiles:
        return None

    total = sum(int(p["count"]) for p in profiles)
    age_buckets: dict[str, float] = defaultdict(float)
    for prof in profiles:
        c = int(prof["count"])
        for key in ("age_under25", "age_25to34", "age_35to44", "age_45plus"):
            val = prof.get(key)
            if val is not None:
                age_buckets[key] += c * val / 100.0

    def merge_field(field: str) -> dict[str, float]:
        return _merge_weighted_distributions(
            [(p.get(field) or {}, int(p["count"])) for p in profiles]
        )

    med, _ = rollup_demographics(demographics, program_ids)
    return {
        "label": label,
        "count": total,
        "gender": merge_field("gender"),
        "race": merge_field("race"),
        "minority": merge_field("minority"),
        "maritalstatus": merge_field("maritalstatus"),
        "lineofbusiness": merge_field("lineofbusiness"),
        "regions": merge_field("regions"),
        "age_median": med,
        "age_under25": round(age_buckets["age_under25"] / total * 100, 1),
        "age_25to34": round(age_buckets["age_25to34"] / total * 100, 1),
        "age_35to44": round(age_buckets["age_35to44"] / total * 100, 1),
        "age_45plus": round(age_buckets["age_45plus"] / total * 100, 1),
    }


def aggregate_monthly_series(
    monthly_by_program: dict,
    program_ids: list[str],
    months: list[str],
) -> list[dict]:
    """Sum monthly funnel metrics across programs for level totals."""
    totals: dict[str, dict] = {
        m: {
            "month": m,
            "leads": 0,
            "apps_started": 0,
            "apps_submitted": 0,
            "decisions": 0,
            "new_enrollments": 0,
        }
        for m in months
    }
    for pid in program_ids:
        for row in monthly_by_program.get(pid) or []:
            m = row.get("month")
            if m not in totals:
                continue
            for key in (
                "leads",
                "apps_started",
                "apps_submitted",
                "decisions",
                "new_enrollments",
            ):
                totals[m][key] += int(row.get(key) or 0)
    return [totals[m] for m in months if m in totals]


def rollup_demographics(
    demographics: dict,
    program_ids: list[str],
) -> tuple[float | None, float | None]:
    """Enrollment-weighted median age (approx) and % female for rolled-up row."""
    total = 0
    female_n = 0
    age_weighted = 0.0
    for pid in program_ids:
        prof = demographics.get(pid)
        if not prof or not prof.get("count"):
            continue
        c = prof["count"]
        total += c
        female = pct_from_dist(prof.get("gender", {}), "Female")
        if female is not None:
            female_n += round(c * female / 100)
        if prof.get("age_median") is not None:
            age_weighted += c * prof["age_median"]
    if total == 0:
        return None, None
    med = round(age_weighted / total)
    fem_pct = round(female_n / total * 100, 1) if total else None
    return med, fem_pct


def net_enrollment_pct(mig: dict | None, enrollment_view_fn) -> float | None:
    ev = enrollment_view_fn(mig)
    if not ev:
        return None
    return ev.get("net_pct_enrollments")


def aggregate_sankey_flow(
    sankey_by_program: dict,
    program_ids: list[str],
) -> dict:
    """Sum segment inflow and funnel stages across programs (level-total Sankey)."""
    seg_counts: dict[str, int] = defaultdict(int)
    funnel_keys = ("inquiries", "app_starts", "app_submits", "decisions", "enrollments")
    funnel = {k: 0 for k in funnel_keys}
    for pid in program_ids:
        block = sankey_by_program.get(pid) or {}
        for seg in block.get("segments") or []:
            name = seg.get("segment")
            if name:
                seg_counts[str(name)] += int(seg.get("leads") or 0)
        f = block.get("funnel") or {}
        for key in funnel_keys:
            funnel[key] += int(f.get(key) or 0)
    segments = [
        {"segment": name, "leads": seg_counts[name]}
        for name in SEGMENT1_ORDER
        if seg_counts.get(name, 0) > 0
    ]
    for name in sorted(seg_counts.keys()):
        if name not in SEGMENT1_ORDER and seg_counts[name] > 0:
            segments.append({"segment": name, "leads": seg_counts[name]})
    return {"segments": segments, "funnel": funnel}


def marketing_widgets_from_sankey_flow(flow: dict) -> dict:
    """Lead-only marketing mix from aggregated Sankey segment inflow (no per-program widgets)."""
    rollup_leads: dict[str, int] = defaultdict(int)
    paid_leads: dict[str, int] = defaultdict(int)
    for seg in flow.get("segments") or []:
        name = (seg.get("segment") or "").strip()
        leads = int(seg.get("leads") or 0)
        if not name or leads <= 0:
            continue
        rollup = SEGMENT1_TO_MARKETING_ROLLUP.get(name)
        if not rollup:
            continue
        rollup_leads[rollup] += leads
        if rollup == "Paid":
            paid_leads[name] += leads
    rl_rows, rl_total = _pct_distribution(dict(rollup_leads), MARKETING_ROLLUP_ORDER)
    pl_rows, pl_total = _pct_distribution(dict(paid_leads), SEGMENT1_ORDER)
    if not rl_rows:
        return {}
    return {
        "marketing_segment": {
            "rollup_leads": rl_rows,
            "rollup_leads_total": rl_total,
            "rollup_enrollments": [],
            "rollup_enrollments_total": 0,
            "paid_leads_breakdown": pl_rows,
            "paid_leads_total": pl_total,
            "paid_enrollment_breakdown": [],
            "paid_enrollments_total": 0,
        },
        "enrollment_lob": {"buckets": [], "total": 0},
    }


def render_sankey_host(
    pid: str,
    flow: dict | None,
    *,
    level_aggregate: bool = False,
    undecided_aggregate: bool = False,
) -> str:
    f = (flow or {}).get("funnel", {})
    if not f or f.get("inquiries", 0) <= 0:
        return ""
    safe = pid.replace("'", "")
    footnote = (
        "Marketing segment "
        "(<code>initial_marketing_segment1</code>: Display, Affiliate, Organic B2C, "
        "Organic B2B, etc.) flows into inquiries, then through the funnel; "
        "gray branches are drop-offs. Width = volume. Labels show % of the "
        "<strong>prior stage</strong> so each split (forward + drop-off) sums to 100% "
        "(segment inflow = % of segment leads; inquiries onward = % of parent stage)."
    )
    if undecided_aggregate:
        footnote += (
            " Segment and funnel volumes are summed across all undecided "
            "inquiry-placeholder programs for the primary reporting window."
        )
    elif level_aggregate:
        footnote += (
            " Segment and funnel volumes are summed across all programs at this "
            "degree level for the primary reporting window."
        )
    return (
        '<div class="card sankey-card">\n'
        '<h4>Lead inflow &amp; funnel (Sankey)</h4>\n'
        f'<p class="flow-footnote">{footnote}</p>\n'
        f'<div class="sankey-host" id="sankey-{safe}" data-pid="{safe}"></div>\n'
        "</div>\n"
    )


def rolling_mean(values: list[int | float], window: int = 4) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        if i < window - 1:
            out.append(None)
        else:
            chunk = values[i - window + 1 : i + 1]
            out.append(sum(chunk) / window)
    return out


def _nice_axis_max(value: float) -> int:
    """Round up to a readable axis ceiling for lead volume."""
    if value <= 0:
        return 1
    n = int(value * 1.08) + 1
    if n <= 500:
        return ((n + 49) // 50) * 50
    if n <= 2000:
        return ((n + 99) // 100) * 100
    return ((n + 499) // 500) * 500


def _monthly_combo_chart_svg(
    months_data: list[dict],
    leads: list[int],
    rolling: list[float | None],
) -> str:
    """Single-scale SVG: bars + rolling line share the same leads axis."""
    n = len(months_data)
    bar_slot = 32
    bar_w = 18
    ml, mr, mt, mb = 46, 10, 10, 30
    plot_h = 200
    width = ml + n * bar_slot + mr
    height = mt + plot_h + mb

    raw_max = float(max(leads) if leads else 1)
    for v in rolling:
        if v is not None:
            raw_max = max(raw_max, v)
    axis_max = _nice_axis_max(raw_max)

    def y_px(val: float) -> float:
        return mt + plot_h - (val / axis_max * plot_h)

    ticks = [0]
    mid = axis_max // 2
    if mid > 0 and mid < axis_max:
        ticks.append(mid)
    ticks.append(axis_max)

    parts: list[str] = [
        f'<svg class="monthly-combo-chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Monthly leads with four-month rolling average">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="14" y="{mt + plot_h / 2:.1f}" transform="rotate(-90 14 {mt + plot_h / 2:.1f})" '
        'text-anchor="middle" class="monthly-axis-title">Leads</text>',
    ]

    for tick in ticks:
        y = y_px(tick)
        parts.append(
            f'<line x1="{ml}" y1="{y:.1f}" x2="{width - mr}" y2="{y:.1f}" '
            'class="monthly-grid-line"/>'
        )
        label = f"{tick:,}" if tick >= 1000 else str(tick)
        parts.append(
            f'<text x="{ml - 6}" y="{y:.1f}" text-anchor="end" '
            f'dominant-baseline="middle" class="monthly-y-label">{label}</text>'
        )

    for i, count in enumerate(leads):
        x = ml + i * bar_slot + (bar_slot - bar_w) / 2
        top = y_px(count)
        bar_height = mt + plot_h - top
        month = months_data[i]["month"]
        parts.append(
            f'<rect x="{x:.1f}" y="{top:.1f}" width="{bar_w}" height="{bar_height:.1f}" '
            f'class="monthly-bar" rx="1">'
            f'<title>{month}: {count:,} leads</title></rect>'
        )
        parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 8}" text-anchor="middle" '
            f'class="monthly-x-label">{month[2:]}</text>'
        )

    line_pts: list[str] = []
    for i, avg in enumerate(rolling):
        if avg is None:
            continue
        cx = ml + i * bar_slot + bar_slot / 2
        cy = y_px(avg)
        line_pts.append(f"{cx:.1f},{cy:.1f}")
    if len(line_pts) >= 2:
        parts.append(
            f'<polyline class="monthly-trend-line" points="{" ".join(line_pts)}"/>'
        )
        for pt in line_pts:
            cx, cy = pt.split(",")
            parts.append(f'<circle class="monthly-trend-dot" cx="{cx}" cy="{cy}" r="3"/>')

    parts.append("</svg>")
    return "".join(parts)


def render_monthly_volume_section(
    months_data: list[dict],
    monthly_label: str,
) -> str:
    if not months_data:
        return ""

    leads = [m["leads"] for m in months_data]
    rolling = rolling_mean(leads, 4)

    h = '        <div class="chart-container monthly-trend">\n'
    h += (
        '        <h4 style="margin-bottom:0.5rem; color:var(--uagc-dark)">'
        f"Monthly volume ({monthly_label})</h4>\n"
    )
    h += '        <div class="monthly-trend-body">\n'
    h += '        <div class="monthly-chart-panel">\n'
    h += _monthly_combo_chart_svg(months_data, leads, rolling)
    h += (
        '        <div class="monthly-chart-legend">'
        '<span class="monthly-legend-bar">Bars: monthly leads</span>'
        '<span class="monthly-legend-line">Line: 4-month rolling avg (from month 4)</span>'
        "</div>\n"
    )
    h += "        </div>\n"

    h += '        <div class="trend-table-wrap">\n'
    h += '        <table class="trend-table">\n'
    h += (
        "<thead><tr><th>Month</th><th>Leads</th><th>App Starts</th>"
        "<th>Submitted</th><th>Decisions</th><th>Enrollments</th>"
        "<th>App Start %</th><th>Decision %</th><th>Enroll %</th></tr></thead>\n"
        "<tbody>\n"
    )
    for m in months_data:
        leads = m["leads"]
        app_pct = (m["apps_started"] / leads * 100) if leads else 0
        dec_pct = (m["decisions"] / leads * 100) if leads else 0
        enr_pct = (m["new_enrollments"] / leads * 100) if leads else 0
        h += (
            f'        <tr><td>{m["month"]}</td><td>{leads:,}</td>'
            f'<td>{m["apps_started"]:,}</td><td>{m["apps_submitted"]:,}</td>'
            f'<td>{m["decisions"]:,}</td><td>{m["new_enrollments"]:,}</td>'
            f"<td>{app_pct:.1f}%</td><td>{dec_pct:.1f}%</td>"
            f"<td>{enr_pct:.1f}%</td></tr>\n"
        )
    h += "        </tbody></table>\n"
    h += "        </div>\n"
    h += "        </div>\n\n"
    return h


def render_state_region_section(
    prof: dict | None,
    baselines: dict,
    degree_level: str,
    *,
    embedded: bool = False,
) -> str:
    if not prof or not prof.get("regions"):
        return ""

    baseline_key = (
        "undergraduate_regions"
        if degree_level == "Undergraduate"
        else "graduate_regions"
    )
    base_regions = baselines.get(baseline_key) or baselines.get("all_regions") or {}
    regions = prof["regions"]
    footnote = (
        "US region share of enrolled students (matric window). "
        "Darker blue = higher index vs same degree-level baseline (100 = typical); "
        "callouts show % share and index."
    )
    map_html = render_us_region_map_html(regions, base_regions, compact=embedded)

    if embedded:
        h = '<div class="widget-geo-embed">\n'
        h += "<h5>Enrollment geography</h5>\n"
        h += f'<p class="flow-footnote">{footnote}</p>\n'
        h += map_html
        h += "</div>\n"
        return h

    h = '<div class="card region-card">\n'
    h += "<h4>Enrollment geography</h4>\n"
    h += f'<p class="flow-footnote">{footnote}</p>\n'
    h += map_html
    h += "</div>\n"
    return h


SANKEY_INFLOW_JS = r"""
function renderInflowSankey(containerId, payload) {
  const el = document.getElementById(containerId);
  if (!el || !payload) return;
  const F = payload.funnel || {};
  const segments = payload.segments || [];
  const inq = F.inquiries || 0;
  if (!inq || !segments.length) return;
  el.innerHTML = '';
  const width = el.clientWidth || 900;
  const height = 400;
  const nodes = [];
  const links = [];
  const segSum = segments.reduce((a, s) => a + (s.leads || 0), 0);
  const pctOf = (num, den) => (den > 0 ? (num / den) * 100 : null);
  const fmtPct = (pct) => {
    if (pct == null || isNaN(pct)) return '';
    if (pct > 0 && pct < 0.5) return '<1%';
    return Math.round(pct) + '%';
  };
  const labelWithPct = (name, pct) => {
    const s = fmtPct(pct);
    return s ? name + ' ' + s : name;
  };

  segments.forEach((s) => {
    nodes.push({
      name: s.segment,
      pct: pctOf(s.leads || 0, segSum),
    });
  });
  const inqIdx = nodes.length;
  nodes.push({ name: 'Inquiries' });
  const appStartIdx = nodes.length;
  const appStarts = F.app_starts || 0;
  nodes.push({ name: 'App Starts', pct: pctOf(appStarts, inq) });
  const appSubIdx = nodes.length;
  const appSubs = F.app_submits || 0;
  nodes.push({ name: 'App Submits', pct: pctOf(appSubs, appStarts) });
  const decIdx = nodes.length;
  const decs = F.decisions || 0;
  nodes.push({ name: 'Decisions', pct: pctOf(decs, appSubs) });
  const enrIdx = nodes.length;
  const enrs = F.enrollments || 0;
  nodes.push({ name: 'Enrollments', pct: pctOf(enrs, decs) });
  const dropNoApp = nodes.length;
  const d0 = inq - appStarts;
  nodes.push({ name: 'No App Started', pct: pctOf(d0, inq) });
  const dropNoSub = nodes.length;
  const d1 = appStarts - appSubs;
  nodes.push({ name: 'Not Submitted', pct: pctOf(d1, appStarts) });
  const dropNoDec = nodes.length;
  const d2 = appSubs - decs;
  nodes.push({ name: 'No Decision', pct: pctOf(d2, appSubs) });
  const dropNoEnr = nodes.length;
  const dropEnr = decs - enrs;
  nodes.push({ name: 'Not Enrolled', pct: pctOf(dropEnr, decs) });
  const segScale = segSum > 0 ? inq / segSum : 1;
  segments.forEach((s, i) => {
    const v = (s.leads || 0) * segScale;
    if (v > 0) links.push({ source: i, target: inqIdx, value: v });
  });
  if (appStarts > 0) links.push({ source: inqIdx, target: appStartIdx, value: appStarts });
  if (d0 > 0) links.push({ source: inqIdx, target: dropNoApp, value: d0 });
  if (appSubs > 0) links.push({ source: appStartIdx, target: appSubIdx, value: appSubs });
  if (d1 > 0) links.push({ source: appStartIdx, target: dropNoSub, value: d1 });
  if (decs > 0) links.push({ source: appSubIdx, target: decIdx, value: decs });
  if (d2 > 0) links.push({ source: appSubIdx, target: dropNoDec, value: d2 });
  if (enrs > 0) links.push({ source: decIdx, target: enrIdx, value: enrs });
  if (dropEnr > 0) links.push({ source: decIdx, target: dropNoEnr, value: dropEnr });

  const sk = window.reportSankey;
  if (!sk || typeof sk.sankey !== 'function') {
    el.innerHTML = '<p class="demo-empty">Sankey layout library unavailable.</p>';
    return;
  }
  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height);
  const sankey = sk.sankey()
    .nodeWidth(16)
    .nodePadding(8)
    .extent([[10, 10], [width - 10, height - 10]])
    .nodeAlign(sk.sankeyLeft);
  let graph;
  try {
    graph = sankey({
      nodes: nodes.map(d => Object.assign({}, d)),
      links: links.map(d => Object.assign({}, d)),
    });
  } catch (err) {
    el.innerHTML = '<p class="demo-empty">Unable to draw Sankey: ' + err.message + '</p>';
    console.error('Sankey error', containerId, err);
    return;
  }
  const segColors = ['#0076A8','#81D3EB','#378DBD','#98A4AE','#0C234B','#AB0520','#0076A8'];
  const stageColors = ['#0C234B','#0076A8','#378DBD','#AB0520','#98A4AE'];
  const dropColor = '#D0D0CE';
  svg.append('g').selectAll('rect').data(graph.nodes).join('rect')
    .attr('x', d => d.x0).attr('y', d => d.y0)
    .attr('height', d => Math.max(1, d.y1 - d.y0))
    .attr('width', d => d.x1 - d.x0)
    .attr('fill', (d, i) => {
      if (i < segments.length) return segColors[i % segColors.length];
      if (i >= dropNoApp) return dropColor;
      const si = i - segments.length;
      return stageColors[si] || '#64748b';
    })
    .attr('opacity', 0.92);
  svg.append('g').attr('fill', 'none').selectAll('path').data(graph.links).join('path')
    .attr('d', sk.sankeyLinkHorizontal())
    .attr('stroke', '#98A4AE')
    .attr('stroke-opacity', 0.4)
    .attr('stroke-width', d => Math.max(1, d.width));
  svg.append('g').selectAll('text').data(graph.nodes).join('text')
    .attr('x', d => d.x0 < width / 2 ? d.x1 + 5 : d.x0 - 5)
    .attr('y', d => (d.y0 + d.y1) / 2)
    .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
    .attr('dy', '0.35em')
    .text(d => labelWithPct(d.name, d.pct))
    .attr('font-size', '10px')
    .attr('fill', '#53565A');
}
function initReportSankeys() {
  if (typeof d3 === 'undefined' || typeof d3.select !== 'function' || !window.reportSankey) {
    document.querySelectorAll('.sankey-host').forEach(function(host) {
      host.innerHTML = '<p class="demo-empty">Chart libraries did not load (check network / CDN).</p>';
    });
    return;
  }
  const data = window.REPORT_SANKEY_DATA || {};
  document.querySelectorAll('.sankey-host').forEach(function(host) {
    const pid = host.dataset.pid;
    if (data[pid]) renderInflowSankey(host.id, data[pid]);
  });
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initReportSankeys);
} else {
  initReportSankeys();
}
"""


# Composition visuals (100% distributions) — labels on bar + aligned under segments
GENDER_COLORS = {
    "Female": "#AB0520",
    "Male": "#0C234B",
}
LOB_DEMO_COLORS = {
    "Core": "#0C234B",
    "FTG": "#AB0520",
    "TB": "#0076A8",
    "Military": "#98A4AE",
}
MARITAL_COLORS = {
    "Single": "#0C234B",
    "Married": "#AB0520",
    "Divorced": "#378DBD",
}
RACE_COLORS = {
    "Black": "#0C234B",
    "White": "#98A4AE",
    "Hispanic": "#378DBD",
    "Other": "#81D3EB",
}
# Low → high transfer credits (undergraduate matriculation bands)
TRANSFER_CREDIT_COLORS = {
    "True Zero": "#D0D0CE",
    "Not True Zero": "#98A4AE",
    "1 to 15 Credits": "#81D3EB",
    "16 to 30 Credits": "#378DBD",
    "31 to 45 Credits": "#0076A8",
    "46 to 60 Credits": "#0C234B",
    "61+ Credits": "#AB0520",
}
_LIGHT_SEGMENT_BG = frozenset({
    "#98A4AE",
    "#81D3EB",
    "#D0D0CE",
    "#f4f4f3",
    TRANSFER_CREDIT_COLORS["True Zero"],
    TRANSFER_CREDIT_COLORS["Not True Zero"],
})


def _composition_items(
    dist: dict[str, float] | None,
    rows: list[dict] | None,
    max_items: int,
) -> list[tuple[str, float]]:
    if rows:
        items = [
            (r["label"], float(r["pct"]))
            for r in rows[:max_items]
            if r.get("pct", 0) > 0
        ]
    elif dist:
        items = [(k, v) for k, v in dist.items() if v > 0]
        if len(items) > max_items:
            items = sorted(items, key=lambda x: -x[1])[:max_items]
    else:
        return []
    return items


def _segment_color(
    label: str,
    colors: dict[str, str] | None,
    palette: list[str] | None,
    index: int,
) -> str:
    if colors and label in colors:
        return colors[label]
    if palette:
        return palette[index % len(palette)]
    return "#94a3b8"


def _segment_text_color(bg: str) -> str:
    return "#0C234B" if bg in _LIGHT_SEGMENT_BG else "#ffffff"


def _seg_bar_label(label: str, pct: float) -> str:
    """Label text rendered inside the bar segment (no external legend)."""
    if pct >= 15:
        return f"{label} {pct:.0f}%"
    return (
        f'<span class="comp-lbl">{label}</span>'
        f'<span class="comp-pct">{pct:.0f}%</span>'
    )


def render_composition_strip(
    dist: dict[str, float] | None = None,
    *,
    rows: list[dict] | None = None,
    colors: dict[str, str] | None = None,
    palette: list[str] | None = None,
    max_items: int = 8,
    min_inline_pct: float = 10.0,  # unused; kept for call-site compatibility
    aria_label: str = "Share breakdown",
) -> str:
    """Single 100% bar with every label inside segments (no legend row)."""
    del min_inline_pct
    items = _composition_items(dist, rows, max_items)
    if not items:
        return '<p class="demo-empty">No data</p>'

    h = f'<div class="comp-strip" role="group" aria-label="{aria_label}">\n'
    h += '<div class="comp-bar" role="img">\n'
    for i, (label, pct) in enumerate(items):
        color = _segment_color(label, colors, palette, i)
        text_color = _segment_text_color(color)
        grow = max(1, int(round(pct * 10)))
        narrow = " comp-seg--narrow" if pct < 14 else ""
        inner = _seg_bar_label(label, pct)
        h += (
            f'<div class="comp-seg{narrow}" style="flex:{grow} 1 0;background:{color};" '
            f'title="{label}: {pct:.1f}%">'
            f'<span class="comp-seg-in" style="color:{text_color};">{inner}</span></div>\n'
        )
    h += "</div></div>\n"
    return h


def sankey_script_block(sankey_by_pid: dict) -> str:
    payload = {
        pid: flow
        for pid, flow in sankey_by_pid.items()
        if flow and (flow.get("funnel") or {}).get("inquiries", 0) > 0
    }
    return (
        '<script src="https://d3js.org/d3.v7.min.js"></script>\n'
        "<script>window.__d3v7 = window.d3;</script>\n"
        '<script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>\n'
        "<script>\n"
        "(function() {\n"
        "  window.reportSankey = {\n"
        "    sankey: window.d3.sankey,\n"
        "    sankeyLinkHorizontal: window.d3.sankeyLinkHorizontal,\n"
        "    sankeyLeft: window.d3.sankeyLeft,\n"
        "  };\n"
        "  window.d3 = window.__d3v7;\n"
        "})();\n"
        "</script>\n"
        f"<script>window.REPORT_SANKEY_DATA = {json.dumps(payload)};</script>\n"
        f"<script>{SANKEY_INFLOW_JS}</script>\n"
    )
