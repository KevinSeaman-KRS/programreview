"""Generate prose program summaries for detail pages."""
from __future__ import annotations

from marketing_segment_hierarchy import MARKETING_ROLLUP_ORDER
from report_demographics import (
    LOB_DISPLAY_LABELS,
    display_gender,
    display_lineofbusiness,
    display_race,
    index_delta_note,
    index_vs_baseline,
    pct_from_dist,
)
from report_html_sections import (
    GRADUATE_TOTAL_ID,
    LEVEL_DETAIL_LABELS,
    UNDERGRAD_TOTAL_ID,
    pct_core_from_widgets,
)

LOB_WIDGET_LABELS = ("Core", "Full Tuition Grant", "Tuition Benefit", "Military")
ROLLUP_COMPARE_THRESHOLD_PCT = 3.0


def _rank_label(rank: int, total: int) -> str:
    if total <= 1:
        return "the only program in its peer set"
    pct = rank / total * 100
    if pct <= 20:
        return f"top-tier (#{rank} of {total})"
    if pct <= 50:
        return f"above median (#{rank} of {total})"
    if pct <= 80:
        return f"below median (#{rank} of {total})"
    return f"lower volume (#{rank} of {total})"


def _level_id(degree_level: str) -> str:
    return (
        UNDERGRAD_TOTAL_ID
        if degree_level == "Undergraduate"
        else GRADUATE_TOTAL_ID
    )


def _level_label(degree_level: str) -> str:
    return LEVEL_DETAIL_LABELS.get(_level_id(degree_level), "level total").lower()


def _rollup_lead_pcts(widgets: dict, pid: str) -> dict[str, float]:
    rows = widgets.get(pid, {}).get("marketing_segment", {}).get("rollup_leads", [])
    return {r["label"]: r["pct"] for r in rows}


def _rollup_enrollment_pcts(widgets: dict, pid: str) -> dict[str, float]:
    rows = widgets.get(pid, {}).get("marketing_segment", {}).get(
        "rollup_enrollments", []
    )
    return {r["label"]: r["pct"] for r in rows}


def _top_marketing_rollup(widgets: dict, pid: str) -> tuple[str, float] | None:
    pcts = _rollup_lead_pcts(widgets, pid)
    if not pcts:
        return None
    label = max(pcts, key=pcts.get)
    return label, pcts[label]


def _top_segment_rollup(widgets: dict, pid: str) -> tuple[str, float] | None:
    seg = widgets.get(pid, {}).get("marketing_segment", {})
    leads = seg.get("leads", [])
    if not leads:
        return None
    top = max(leads, key=lambda x: x["pct"])
    return top["label"], top["pct"]


def _lob_buckets(widgets: dict, pid: str) -> list[dict]:
    return widgets.get(pid, {}).get("enrollment_lob", {}).get("buckets", [])


def _dominant_lob(widgets: dict, pid: str) -> tuple[str, str, float, int] | None:
    """Return (full_label, short_label, pct, count)."""
    buckets = _lob_buckets(widgets, pid)
    if not buckets:
        return None
    top = max(buckets, key=lambda x: x["pct"])
    short = LOB_DISPLAY_LABELS.get(top["label"], top["label"])
    return top["label"], short, top["pct"], int(top.get("count", 0) or 0)


def _lob_pct(widgets: dict, pid: str, lob_label: str) -> float | None:
    for b in _lob_buckets(widgets, pid):
        if b.get("label") == lob_label:
            return b["pct"]
    return None


def _lob_count(widgets: dict, pid: str, lob_label: str) -> int:
    for b in _lob_buckets(widgets, pid):
        if b.get("label") == lob_label:
            return int(b.get("count", 0) or 0)
    return 0


def _rollup_compare_bits(
    prog_pcts: dict[str, float],
    level_pcts: dict[str, float],
    *,
    threshold: float = ROLLUP_COMPARE_THRESHOLD_PCT,
) -> list[str]:
    bits: list[str] = []
    for label in MARKETING_ROLLUP_ORDER:
        prog = prog_pcts.get(label)
        level = level_pcts.get(label)
        if prog is None or level is None:
            continue
        delta = prog - level
        if abs(delta) < threshold:
            continue
        direction = "above" if delta > 0 else "below"
        bits.append(
            f"<strong>{label}</strong> {prog:.0f}% ({direction} {level:.0f}% "
            f"for the level by {abs(delta):.0f} pts)"
        )
    return bits


def _lead_sources_paragraph(
    pid: str,
    widgets: dict,
    level_id: str,
    level_name: str,
    nav_pct: float | None,
) -> str:
    prog_leads = _rollup_lead_pcts(widgets, pid)
    level_leads = _rollup_lead_pcts(widgets, level_id)
    if not prog_leads:
        return ""

    seg_top = _top_segment_rollup(widgets, pid)
    rollup_top = _top_marketing_rollup(widgets, pid)

    lines: list[str] = []
    if rollup_top:
        lines.append(f"{rollup_top[0]} ({rollup_top[1]:.1f}% of program leads)")
    if seg_top:
        lines.append(f"largest segment {seg_top[0]} ({seg_top[1]:.1f}% of leads)")
    if nav_pct is not None:
        lines.append(f"Navigational share of final enrollments {nav_pct:.0f}%")

    body = "; ".join(lines)
    compare_bits = _rollup_compare_bits(prog_leads, level_leads)
    if compare_bits:
        body += (
            f". Versus <strong>{level_name}</strong> lead mix: "
            + "; ".join(compare_bits)
        )

    prog_enr = _rollup_enrollment_pcts(widgets, pid)
    level_enr = _rollup_enrollment_pcts(widgets, level_id)
    enr_bits = _rollup_compare_bits(prog_enr, level_enr)
    if enr_bits:
        body += (
            ". Final-enrollment mix differs from level leads: "
            + "; ".join(enr_bits)
        )

    return f"<p><strong>Lead sources:</strong> {body}.</p>"


def _lob_context_paragraph(
    pid: str,
    program_name: str,
    peers: list[dict],
    widgets: dict,
    level_id: str,
    level_name: str,
    baseline_key: str,
    demo_baselines: dict,
) -> str:
    dom = _dominant_lob(widgets, pid)
    if not dom:
        return ""

    full_label, short_label, dom_pct, dom_count = dom
    lob_total = int(
        widgets.get(pid, {}).get("enrollment_lob", {}).get("total", 0) or 0
    )
    level_pct = _lob_pct(widgets, level_id, full_label)
    baseline = demo_baselines.get(baseline_key) or {}
    base_lob = display_lineofbusiness(baseline.get("lineofbusiness", {})).get(
        short_label
    )

    bits: list[str] = [
        f"Dominant matriculation LOB is <strong>{short_label}</strong> "
        f"({dom_pct:.1f}% of {lob_total:,} enrolled students; {dom_count:,} in {short_label})"
    ]
    if level_pct is not None:
        lob_note = index_delta_note(dom_pct, level_pct)
        bits.append(
            f"{lob_note} the {level_name} share for {short_label} ({level_pct:.1f}%)"
        )
    if base_lob is not None:
        bits.append(
            f"{index_delta_note(dom_pct, base_lob)} enrolled-student baseline "
            f"for {short_label} ({base_lob:.1f}%)"
        )

    ranked = sorted(
        (
            (peer["program_name"], _lob_count(widgets, peer["program_id"], full_label))
            for peer in peers
        ),
        key=lambda x: (-x[1], x[0]),
    )
    ranked = [(name, n) for name, n in ranked if n > 0]
    if ranked:
        top_show = ranked[:5]
        top_lines = ", ".join(
            f"<strong>{name}</strong> ({n:,})" for name, n in top_show
        )
        rank = next(
            (i + 1 for i, (name, _) in enumerate(ranked) if name == program_name),
            None,
        )
        bits.append(
            f"top {short_label} programs by gross matriculations: {top_lines}"
        )
        if rank is not None:
            bits.append(f"this program ranks <strong>#{rank}</strong> for {short_label}")

    return f"<p><strong>Enrollment mix (LOB):</strong> {'; '.join(bits)}.</p>"


def _additional_context_paragraph(
    p: dict,
    level_ref: dict | None,
    level_name: str,
    widgets: dict,
    pid: str,
) -> str:
    if not level_ref:
        return ""

    leads = p.get("leads", 0) or 0
    enr = p.get("new_enrollments", 0) or 0
    level_leads = level_ref.get("leads", 0) or 0
    level_enr = level_ref.get("new_enrollments", 0) or 0
    if level_leads <= 0:
        return ""

    level_id = level_ref.get("program_id")

    enr_rate = (enr / leads * 100) if leads else 0
    level_rate = (level_enr / level_leads * 100) if level_leads else 0
    lead_share = leads / level_leads * 100
    enr_share = (enr / level_enr * 100) if level_enr else 0

    bits: list[str] = [
        f"<strong>{lead_share:.1f}%</strong> of {level_name} inquiries "
        f"({leads:,} of {level_leads:,})"
    ]
    if level_enr:
        bits.append(
            f"<strong>{enr_share:.1f}%</strong> of level final enrollments "
            f"({enr:,} of {level_enr:,})"
        )
    if leads and level_rate:
        delta = enr_rate - level_rate
        if abs(delta) >= 0.15:
            direction = "above" if delta > 0 else "below"
            bits.append(
                f"inquiry-to-enrollment <strong>{enr_rate:.2f}%</strong> "
                f"({direction} {level_name} {level_rate:.2f}% by {abs(delta):.2f} pts)"
            )

    dom = _dominant_lob(widgets, pid)
    if dom and level_id:
        _, short_label, dom_pct, _ = dom
        level_pct = _lob_pct(widgets, level_id, dom[0])
        if level_pct is not None and abs(dom_pct - level_pct) >= 5:
            bits.append(
                f"{short_label} concentration {dom_pct:.0f}% vs {level_pct:.0f}% "
                f"for all {level_name} matriculations"
            )

    core_pct = pct_core_from_widgets(widgets, pid)
    level_core = pct_core_from_widgets(widgets, level_id) if level_id else None
    if core_pct is not None and level_core is not None and abs(core_pct - level_core) >= 5:
        bits.append(
            f"Core LOB share <strong>{core_pct:.1f}%</strong> vs "
            f"{level_core:.1f}% for {level_name}"
        )

    if not bits:
        return ""

    return f"<p><strong>Compared to {level_name}:</strong> {'; '.join(bits)}.</p>"


def _top_region(prof: dict | None) -> tuple[str, float] | None:
    if not prof or not prof.get("regions"):
        return None
    region, pct = max(prof["regions"].items(), key=lambda x: x[1])
    return region, pct


def _profile_vs_baseline_paragraph(
    prof: dict,
    baseline: dict,
    baseline_key: str,
    detail_widgets: dict,
    pid: str,
) -> str:
    n = prof.get("count", 0)
    if n <= 0:
        return ""

    bits: list[str] = []

    prog_med = prof.get("age_median")
    base_med = baseline.get("age_median")
    if prog_med is not None and base_med is not None:
        age_note = index_delta_note(float(prog_med), float(base_med))
        if age_note == "in line with":
            bits.append(
                f"median age <strong>{prog_med}</strong> matches the {baseline_key} "
                f"enrolled average ({base_med})"
            )
        else:
            bits.append(
                f"median age <strong>{prog_med}</strong> is {age_note} the {baseline_key} "
                f"average ({base_med})"
            )

    gender_d = display_gender(prof.get("gender", {}))
    female = gender_d.get("Female")
    base_gender_d = display_gender(baseline.get("gender", {}))
    base_female = base_gender_d.get("Female")
    if female is not None and base_female is not None:
        f_idx = index_vs_baseline(female, base_female)
        fem_note = index_delta_note(female, base_female)
        idx_clause = ""
        if f_idx is not None:
            if f_idx > 110:
                idx_clause = " — a notably more female cohort"
            elif f_idx < 90:
                idx_clause = " — a notably more male cohort"
            elif f_idx != 100:
                idx_clause = f" (index {f_idx} vs level baseline)"
        bits.append(
            f"<strong>{female:.1f}%</strong> female, {fem_note} the {baseline_key} "
            f"share ({base_female:.1f}%){idx_clause}"
        )

    race_d = display_race(prof.get("race", {}))
    base_race_d = display_race(baseline.get("race", {}))
    if race_d:
        top_race = max(race_d, key=race_d.get)
        top_pct = race_d[top_race]
        base_top_pct = base_race_d.get(top_race)
        race_note = index_delta_note(top_pct, base_top_pct)
        if base_top_pct is not None:
            bits.append(
                f"largest ethnicity group is <strong>{top_race}</strong> ({top_pct:.1f}%), "
                f"{race_note} the {baseline_key} norm for {top_race} ({base_top_pct:.1f}%)"
            )
        else:
            bits.append(
                f"largest ethnicity group is <strong>{top_race}</strong> ({top_pct:.1f}%)"
            )

    lob_d = display_lineofbusiness(prof.get("lineofbusiness", {}))
    base_lob_d = display_lineofbusiness(baseline.get("lineofbusiness", {}))
    if lob_d:
        top_lob = max(lob_d, key=lob_d.get)
        top_pct = lob_d[top_lob]
        base_pct = base_lob_d.get(top_lob)
        lob_note = index_delta_note(top_pct, base_pct)
        bits.append(
            f"line of business skews to <strong>{top_lob}</strong> ({top_pct:.1f}%), "
            f"{lob_note} typical {baseline_key} mix for {top_lob} ({base_pct:.1f}%)"
            if base_pct is not None
            else f"line of business skews to <strong>{top_lob}</strong> ({top_pct:.1f}%)"
        )

    core_pct = pct_core_from_widgets(detail_widgets, pid)
    base_core = display_lineofbusiness(baseline.get("lineofbusiness", {})).get("Core")
    if core_pct is not None and base_core is not None:
        bits.append(
            f"Core share is <strong>{core_pct:.1f}%</strong> "
            f"({index_delta_note(core_pct, base_core)} {baseline_key} Core at {base_core:.1f}%)"
        )

    if not bits:
        return ""

    return (
        f"<p><strong>How enrollees differ from average:</strong> Among {n:,} matriculants, "
        + "; ".join(bits)
        + f". Comparisons use all {baseline_key} enrolled students in the same window.</p>"
    )


def build_program_summary(
    p: dict,
    peers: list[dict],
    period_primary: str,
    period_prior: str,
    detail_widgets: dict,
    demographics: dict,
    demo_baselines: dict,
    migration: dict,
    enrollment_view_fn,
    *,
    level_ref: dict | None = None,
) -> str:
    pid = p["program_id"]
    name = p["program_name"]
    leads = p.get("leads", 0)
    enr = p.get("new_enrollments", 0)
    enr_rate = (enr / leads * 100) if leads else 0
    degree_level = p.get("degree_level", "")
    level_id = _level_id(degree_level)
    level_name = _level_label(degree_level)
    if level_ref is None:
        level_ref = {"program_id": level_id}

    peer_leads = sorted([x.get("leads", 0) for x in peers], reverse=True)
    rank = peer_leads.index(leads) + 1 if leads in peer_leads else len(peers)
    total_peers = len(peers)

    py_leads = p.get("py_leads", 0)
    if py_leads:
        lead_chg = (leads - py_leads) / py_leads * 100
        lead_trend = (
            f"up {lead_chg:.0f}% vs {period_prior}"
            if lead_chg > 5
            else f"down {abs(lead_chg):.0f}% vs {period_prior}"
            if lead_chg < -5
            else f"flat vs {period_prior}"
        )
    else:
        lead_trend = f"no prior-period baseline in {period_prior}"

    peer_rates = [
        (x.get("new_enrollments", 0) / x["leads"] * 100)
        for x in peers
        if x.get("leads", 0) > 0
    ]
    median_rate = sorted(peer_rates)[len(peer_rates) // 2] if peer_rates else 0
    rate_vs_peers = (
        "above peer median inquiry-to-enrollment rate"
        if enr_rate > median_rate * 1.1
        else "below peer median inquiry-to-enrollment rate"
        if enr_rate < median_rate * 0.9
        else "near the peer median inquiry-to-enrollment rate"
    )

    parts = [
        f"<p><strong>{name}</strong> generated <strong>{leads:,}</strong> inquiries "
        f"in {period_primary} ({lead_trend}), ranking {_rank_label(rank, total_peers)} "
        f"among {total_peers} programs at the same degree level.</p>",
        f"<p>The program recorded <strong>{enr:,}</strong> final enrollments "
        f"({enr_rate:.2f}% of inquiries), {rate_vs_peers} "
        f"(peer median ~{median_rate:.2f}%).</p>",
    ]

    lead_para = _lead_sources_paragraph(
        pid,
        detail_widgets,
        level_id,
        level_name,
        p.get("pct_navigational"),
    )
    if lead_para:
        parts.append(lead_para)

    context_para = _additional_context_paragraph(
        p, level_ref, level_name, detail_widgets, pid
    )
    if context_para:
        parts.append(context_para)

    baseline_key = (
        "undergraduate" if degree_level == "Undergraduate" else "graduate"
    )
    lob_para = _lob_context_paragraph(
        pid,
        name,
        peers,
        detail_widgets,
        level_id,
        level_name,
        baseline_key,
        demo_baselines,
    )
    if lob_para:
        parts.append(lob_para)

    prof = demographics.get(pid)
    baseline = demo_baselines.get(baseline_key) or demo_baselines.get("all") or {}
    if prof and prof.get("count", 0) > 0:
        vs_avg = _profile_vs_baseline_paragraph(
            prof, baseline, baseline_key, detail_widgets, pid
        )
        if vs_avg:
            parts.append(vs_avg)

    region_top = _top_region(prof)
    if region_top:
        parts.append(
            f"<p><strong>Geography:</strong> strongest enrollment region is "
            f"<strong>{region_top[0]}</strong> ({region_top[1]:.1f}% of matriculants).</p>"
        )

    mig = migration.get(pid)
    ev = enrollment_view_fn(mig) if mig else None
    if ev and ev.get("enrollments_in", 0) > 0:
        net = ev.get("net_migration", 0)
        sign = "gains" if net > 0 else "loses" if net < 0 else "shows no net"
        parts.append(
            f"<p><strong>Program migration:</strong> {sign} "
            f"<strong>{abs(net):,}</strong> final enrollments vs same-path inquiry "
            f"({ev.get('same_path_enrollments', 0):,} stayed on-program; "
            f"net {ev.get('net_pct_enrollments', 0):+.1f}% of applied enrollments).</p>"
        )

    return '<div class="card prose-card">\n<h4>Program summary</h4>\n' + "\n".join(parts) + "\n</div>\n"
