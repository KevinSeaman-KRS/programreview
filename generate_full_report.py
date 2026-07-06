"""
Generate full HTML Program Performance Report.
Features:
- Totals / Undergraduate / Graduate tabs in summary matrix (totals default)
- Hyperlinks to detail pages and live website
- KPI scorecards with % change vs PY + directional icons
- Horizontal monthly trend charts (months on x-axis)
- Desktop + mobile screenshots
- Funnel visualization per program
"""
from html import escape as html_escape
import json
import base64
import os
import shutil
from datetime import date
from pathlib import Path

from report_demographics import (
    display_gender,
    display_lineofbusiness,
    display_maritalstatus,
    display_race,
    display_transfer_credits,
    index_delta_note,
    index_vs_baseline,
    pct_from_dist,
)
from program_master_fill import apply_matrix_new_flags, fill_missing_master_programs
from marketing_segment_hierarchy import (
    MARKETING_ROLLUP_COLORS,
    SEGMENT1_COLORS,
    SEGMENT_ROLLUP_COLORS,
)
from report_methodology import render_methodology_appendix
from report_html_sections import (
    GENDER_COLORS,
    LOB_DEMO_COLORS,
    MARITAL_COLORS,
    RACE_COLORS,
    TRANSFER_CREDIT_COLORS,
    UNDERGRAD_TOTAL_ID,
    GRADUATE_TOTAL_ID,
    OVERALL_TOTAL_ID,
    UNDECIDED_ROLLUP_ID,
    UNDECIDED_DETAIL_LABEL,
    LEVEL_DETAIL_LABELS,
    LEVEL_DETAIL_PROGRAM_IDS,
    LEVEL_DETAIL_URLS,
    aggregate_matrix_programs,
    aggregate_monthly_series,
    aggregate_undecided_programs,
    enrich_matrix_rollup_row,
    change_icon_prior,
    is_undecided_program,
    fmt_matrix_count,
    fmt_matrix_pct,
    matrix_lob_enroll_count,
    matrix_age_female,
    CORE_LOB_LABELS,
    MILITARY_LOB_LABELS,
    B2B_LOB_LABELS,
    matrix_military_b2b_pct,
    matrix_top_n_program_ids,
    net_enrollment_pct,
    pct_core_from_widgets,
    render_composition_strip,
    render_sankey_host,
    render_monthly_volume_section,
    render_state_region_section,
    aggregate_sankey_flow,
    marketing_widgets_from_sankey_flow,
    rollup_demographics_profile,
    rollup_detail_widgets,
    sankey_script_block,
)
from report_periods import (
    DEMOGRAPHICS_MATRIC_LABEL,
    MONTHLY_DETAIL_MONTHS,
    PRIMARY_LABEL,
    PRIOR_LABEL,
)
from report_prose_summary import build_program_summary
from report_program_alignment import (
    load_program_alignment,
    render_academic_alignment_section,
    render_organization_nav_tab,
    resolve_alignment_by_program_id,
)

ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "screenshots"

with open(ROOT / "program_data_full.json", encoding="utf-8") as f:
    data = json.load(f)

programs = fill_missing_master_programs(
    data["programs"], ROOT / "data" / "program_srm_bridge.json"
)
apply_matrix_new_flags(programs)
bridge_path = ROOT / "data" / "program_srm_bridge.json"
if bridge_path.exists():
    bridge_programs = json.loads(bridge_path.read_text(encoding="utf-8")).get(
        "programs", []
    )
    account_group_by_pid = {
        bp["program_id"]: bp.get("account_group") or "—" for bp in bridge_programs
    }
    cvue_by_pid = {
        bp["program_id"]: (bp.get("program_code_cvue") or "").strip()
        for bp in bridge_programs
    }
    for p in programs:
        p["account_group"] = account_group_by_pid.get(p["program_id"], "—")
        p["program_code_cvue"] = cvue_by_pid.get(p["program_id"], "")
else:
    for p in programs:
        p["account_group"] = "—"

monthly = data['monthly']
funnel = data['funnel']
primary_label = data.get('primary_period', {}).get('label', PRIMARY_LABEL)
prior_label = data.get('prior_period', {}).get('label', PRIOR_LABEL)
monthly_detail_label = data.get('monthly_detail_period', {}).get(
    'label', 'Apr 2025 – Jun 2026'
)

migration_path = ROOT / "program_migration.json"
if migration_path.exists():
    with open(migration_path, encoding="utf-8") as f:
        migration = json.load(f).get('programs', {})
else:
    migration = {}

demographics_path = ROOT / "program_demographics.json"
if demographics_path.exists():
    with open(demographics_path, encoding="utf-8") as f:
        demo_data = json.load(f)
        demographics = demo_data.get('programs', {})
        demo_baselines = demo_data.get('baselines', {})
        demo_matric_label = demo_data.get('matric_window', {}).get(
            'label', DEMOGRAPHICS_MATRIC_LABEL
        )
else:
    demographics = {}
    demo_baselines = {}
    demo_matric_label = DEMOGRAPHICS_MATRIC_LABEL

widgets_path = ROOT / "program_detail_widgets.json"
if widgets_path.exists():
    with open(widgets_path, encoding="utf-8") as f:
        widgets_meta = json.load(f)
        detail_widgets = widgets_meta.get("programs", {})
        widget_segment_colors = widgets_meta.get("segment_colors", {})
        widget_marketing_rollup_colors = widgets_meta.get(
            "marketing_rollup_colors", {}
        )
        widget_segment1_colors = widgets_meta.get("segment1_colors", {})
        widget_lob_colors = widgets_meta.get("lob_colors", {})
        lob_matric_label = widgets_meta.get("matric_window", {}).get(
            "label", DEMOGRAPHICS_MATRIC_LABEL
        )
else:
    detail_widgets = {}
    widget_segment_colors = {}
    widget_marketing_rollup_colors = {}
    widget_segment1_colors = {}
    widget_lob_colors = {}
    lob_matric_label = DEMOGRAPHICS_MATRIC_LABEL

# Canonical UAGC palette (overrides stale colors embedded in pulled JSON)
WIDGET_LOB_COLORS = {
    "Core": "#0C234B",
    "Full Tuition Grant": "#AB0520",
    "Tuition Benefit": "#0076A8",
    "Military": "#98A4AE",
}
widget_segment_colors = SEGMENT_ROLLUP_COLORS
widget_marketing_rollup_colors = MARKETING_ROLLUP_COLORS
widget_segment1_colors = SEGMENT1_COLORS
widget_lob_colors = WIDGET_LOB_COLORS

sankey_flow_path = ROOT / "program_sankey_flow.json"
if sankey_flow_path.exists():
    with open(sankey_flow_path, encoding="utf-8") as f:
        sankey_flow = json.load(f).get("programs", {})
else:
    sankey_flow = {}

alignment_data = load_program_alignment()
alignment_by_pid: dict[str, dict] = {}

# Program URL mapping
PROGRAM_URLS = {
    '001Do00000ScUyCIAV': 'https://www.uagc.edu/online-degrees/associate/business',
    '001Do00000ScUzUIAV': 'https://www.uagc.edu/online-degrees/associate/early-childhood-education',
    '001Do00000ScUyvIAF': 'https://www.uagc.edu/online-degrees/associate/military-studies',
    '001Do00000ScUyDIAV': 'https://www.uagc.edu/online-degrees/associate/organizational-management',
    '001Do00000ScUyPIAV': 'https://www.uagc.edu/online-degrees/bachelors/accounting',
    '001Do00000ScUzGIAV': 'https://www.uagc.edu/online-degrees/bachelors/applied-behavioral-science',
    '001Do00000ScUyQIAV': 'https://www.uagc.edu/online-degrees/bachelors/business-administration',
    '001Do00000ScUyEIAV': 'https://www.uagc.edu/online-degrees/bachelors/business-economics',
    '001Do00000ScUzHIAV': 'https://www.uagc.edu/online-degrees/bachelors/business-information-systems',
    '001Do00000ScUyRIAV': 'https://www.uagc.edu/online-degrees/bachelors/business-leadership',
    '001Do00000ScUzdIAF': 'https://www.uagc.edu/online-degrees/bachelors/child-development',
    '001Do00000ScUysIAF': 'https://www.uagc.edu/online-degrees/bachelors/communication-studies',
    '001Do00000ScUzeIAF': 'https://www.uagc.edu/online-degrees/bachelors/early-childhood-development-differentiated-instruction',
    '001Do00000ScUzfIAF': 'https://www.uagc.edu/online-degrees/bachelors/early-childhood-education',
    '001Do00000ScUzgIAF': 'https://www.uagc.edu/online-degrees/bachelors/early-childhood-education-administration',
    '001Do00000ScUzhIAF': 'https://www.uagc.edu/online-degrees/bachelors/education-studies',
    '001Do00000ScUySIAV': 'https://www.uagc.edu/online-degrees/bachelors/finance',
    '001Do00000ScUzEIAV': 'https://www.uagc.edu/online-degrees/bachelors/health-human-services',
    '001Do00000ScUyeIAF': 'https://www.uagc.edu/online-degrees/bachelors/health-and-wellness',
    '001Do00000ScUybIAF': 'https://www.uagc.edu/online-degrees/bachelors/health-care-administration',
    '001Do00000ScUz6IAF': 'https://www.uagc.edu/online-degrees/bachelors/homeland-security-emergency-management',
    '001Do00000ScUyXIAV': 'https://www.uagc.edu/online-degrees/bachelors/human-resources-management',
    '001Do00000ScUzZIAV': 'https://www.uagc.edu/online-degrees/bachelors/instructional-design',
    '001Do00000ScUyqIAF': 'https://www.uagc.edu/online-degrees/bachelors/liberal-arts',
    '001Do00000ScUyTIAV': 'https://www.uagc.edu/online-degrees/bachelors/marketing',
    '001Do00000ScUyUIAV': 'https://www.uagc.edu/online-degrees/bachelors/operations-management-analysis',
    '001Do00000ScUyVIAV': 'https://www.uagc.edu/online-degrees/bachelors/organizational-management',
    '001Do00000ScUyWIAV': 'https://www.uagc.edu/online-degrees/bachelors/project-management',
    '001Do00000ScUzFIAV': 'https://www.uagc.edu/online-degrees/bachelors/psychology',
    '001Do00000ScUz7IAF': 'https://www.uagc.edu/online-degrees/bachelors/criminal-justice',
    '001Do00000ScUyzIAF': 'https://www.uagc.edu/online-degrees/bachelors/social-science',
    '001Do00000ScUzCIAV': 'https://www.uagc.edu/online-degrees/bachelors/sociology',
    '001Do00000ScUyNIAV': 'https://www.uagc.edu/online-degrees/bachelors/supply-chain-management',
    '001Do00000ScUzIIAV': 'https://www.uagc.edu/online-degrees/bachelors/computer-software-technology',
    '001Do00000ScUzJIAV': 'https://www.uagc.edu/online-degrees/bachelors/cyber-data-security-technology',
    '001Do00000ScUyaIAF': 'https://www.uagc.edu/online-degrees/bachelors/health-information-management',
    '001Do00000ScUzKIAV': 'https://www.uagc.edu/online-degrees/bachelors/information-technology',
    '001Do00000ScUymIAF': 'https://www.uagc.edu/online-degrees/bachelors/nursing',
    '001Vr00000YtotRIAR': 'https://www.uagc.edu/online-degrees/doctoral/organizational-leadership',
    '001Do00000ScUzbIAF': 'https://www.uagc.edu/online-degrees/masters/early-childhood-education-leadership',
    '001Do00000ScUzcIAF': 'https://www.uagc.edu/online-degrees/masters/education',
    '001Do00000ScUynIAF': 'https://www.uagc.edu/online-degrees/masters/health-care-administration',
    '001Do00000ScUzAIAV': 'https://www.uagc.edu/online-degrees/masters/human-services',
    '001Do00000ScUy8IAF': 'https://www.uagc.edu/online-degrees/masters/organizational-management',
    '001Do00000ScUz9IAF': 'https://www.uagc.edu/online-degrees/masters/psychology',
    '001Do00000ScUzSIAV': 'https://www.uagc.edu/online-degrees/masters/special-education',
    '001Do00000ScUzTIAV': 'https://www.uagc.edu/online-degrees/masters/teaching-and-learning-with-technology',
    '001Do00000ScUyZIAV': 'https://www.uagc.edu/online-degrees/masters/accounting',
    '001Do00000ScUy9IAF': 'https://www.uagc.edu/online-degrees/masters/business-administration',
    '001Do00000ScUyAIAV': 'https://www.uagc.edu/online-degrees/masters/human-resources-management',
    '001Do00000ScUzMIAV': 'https://www.uagc.edu/online-degrees/masters/information-systems-management',
    '001Do00000ScUylIAF': 'https://www.uagc.edu/online-degrees/masters/public-health',
    '001Vr00000t9K7vIAE': 'https://www.uagc.edu/online-degrees/masters/leadership',
    '001Do00000ScUz8IAF': 'https://www.uagc.edu/online-degrees/masters/criminal-justice',
    '001Do00000ScUyBIAV': 'https://www.uagc.edu/online-degrees/masters/finance',
    '001Do00000ScUykIAF': 'https://www.uagc.edu/online-degrees/masters/health-informatics-analytics',
    '001Do00000ScUzQIAV': 'https://www.uagc.edu/online-degrees/masters/instructional-design-technology',
    '001Do00000ScUzNIAV': 'https://www.uagc.edu/online-degrees/masters/technology-management',
    '001Do00000ScUzOIAV': 'https://www.uagc.edu/online-degrees/certificates/post-baccalaureate-teaching',
    '001Do00000YZZzVIAX': 'https://www.uagc.edu/online-degrees/bachelors',
    '001Do00000YZZxZIAX': 'https://www.uagc.edu/online-degrees/business',
    '001Do00000YZZxjIAH': 'https://www.uagc.edu/online-degrees/criminal-justice',
    '001Do00000YZZyXIAX': 'https://www.uagc.edu/online-degrees/education',
    '001Do00000YZZyYIAX': 'https://www.uagc.edu/online-degrees/health-care',
    '001Do00000YZZymIAH': 'https://www.uagc.edu/online-degrees/information-technology',
    '001Do00000YZZz6IAH': 'https://www.uagc.edu/online-degrees/liberal-arts',
    '001Do00000YZZz7IAH': 'https://www.uagc.edu/online-degrees/masters',
    '001Do00000YZZzGIAX': 'https://www.uagc.edu/online-degrees/social-behavioral-science',
    '001Do00000YZZzHIAX': 'https://www.uagc.edu/online-degrees',
}
PROGRAM_URLS.update(LEVEL_DETAIL_URLS)

USE_EXTERNAL_IMAGES = True
DEPLOY_DIR = ROOT / "deploy"

def img_to_base64(filepath):
    if not os.path.exists(filepath):
        return None
    if USE_EXTERNAL_IMAGES:
        return None  # skip base64, use external paths
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def img_src(pid: str, device: str, page: int | str = 1) -> str | None:
    if page == 1 or page == "hero":
        fname = f"{device}_{pid}.png"
    elif page == 2 or page == "mid":
        fname = f"{device}_{pid}_page2.png"
    elif page == "full":
        fname = f"{device}_{pid}_full.png"
    else:
        return None
    if not (SCREENSHOT_DIR / fname).exists():
        return None
    return f"screenshots/{fname}"


def sync_screenshots_to_deploy(program_ids: frozenset[str] | None = None) -> int:
    """Copy PNGs into deploy/screenshots so index.html resolves images."""
    dest = DEPLOY_DIR / "screenshots"
    dest.mkdir(parents=True, exist_ok=True)
    if program_ids:
        for old in dest.glob("*.png"):
            old.unlink()
    n = 0
    if not SCREENSHOT_DIR.is_dir():
        return 0
    for png in SCREENSHOT_DIR.glob("*.png"):
        if program_ids and not any(pid in png.name for pid in program_ids):
            continue
        shutil.copy2(png, dest / png.name)
        n += 1
    return n


def _lp_device_column(
    device: str,
    frames: list[tuple[str, str | None, str]],
) -> str:
    """One device column: tab nav + scrollable viewport."""
    available = [(key, src, label) for key, src, label in frames if src]
    if not available:
        return ""
    default_key, default_src, default_label = available[0]
    for prefer in ("full", "mid", "hero"):
        for key, src, label in available:
            if key == prefer:
                default_key, default_src, default_label = key, src, label
                break
        else:
            continue
        break
    data_attrs = " ".join(
        f'data-{key}="{src}"' for key, src, _ in frames if src
    )
    nav = ""
    for key, src, label in frames:
        if not src:
            continue
        is_default = key == default_key
        active_cls = " is-active" if is_default else ""
        aria = "true" if is_default else "false"
        nav += (
            f'<button type="button" class="lp-nav-btn{active_cls}" '
            f'data-frame="{key}" role="tab" aria-selected="{aria}">'
            f"{label}</button>"
        )
    viewport_cls = "lp-viewport"
    if default_key == "full":
        viewport_cls += " lp-viewport--full"
    else:
        viewport_cls += " lp-viewport--slice"
    device_label = "Desktop" if device == "desktop" else "Mobile"
    device_mod = " lp-device--desktop" if device == "desktop" else " lp-device--mobile"
    return (
        f'            <div class="lp-device{device_mod}" data-device="{device}">\n'
        f'                <div class="lp-device-head">\n'
        f'                    <span class="lp-device-name">{device_label}</span>\n'
        f'                    <div class="lp-nav" role="tablist">{nav}</div>\n'
        f"                </div>\n"
        f'                <div class="{viewport_cls}">\n'
        f'                    <img class="lp-shot" src="{default_src}" alt="{default_label}" '
        f'loading="lazy" {data_attrs}>\n'
        f"                </div>\n"
        f"            </div>\n"
    )


def render_landing_screenshots(pid: str, url: str) -> str:
    desktop_frames = [
        ("hero", img_src(pid, "desktop", 1), "Hero"),
        ("mid", img_src(pid, "desktop", 2), "Careers"),
        ("full", img_src(pid, "desktop", "full"), "Full page"),
    ]
    mobile_frames = [
        ("hero", img_src(pid, "mobile", 1), "Hero"),
        ("mid", img_src(pid, "mobile", 2), "Careers"),
        ("full", img_src(pid, "mobile", "full"), "Full page"),
    ]
    has_any = any(src for _, src, _ in desktop_frames + mobile_frames)
    if not has_any:
        return (
            '        <section class="lp-capture lp-capture--empty">\n'
            '            <div class="lp-capture-header">\n'
            '                <h4>Landing page</h4>\n'
            f'                <a href="{url}" target="_blank" rel="noopener" class="lp-live-link">View live page</a>\n'
            "            </div>\n"
            '            <div class="screenshot-empty">\n'
            f'                <p>No captures yet. Open the <a href="{url}" target="_blank" rel="noopener">'
            "live program page</a>, then refresh assets:</p>\n"
            "                <pre>uvx --with playwright --with pillow python capture_all_screenshots.py</pre>\n"
            "            </div>\n"
            "        </section>\n"
        )

    anchor_id = f"lp-{pid}"
    h = f'        <section class="lp-capture" id="{anchor_id}">\n'
    h += '            <div class="lp-capture-header">\n'
    h += '                <h4>Landing page</h4>\n'
    h += (
        f'                <a href="{url}" target="_blank" rel="noopener" '
        f'class="lp-live-link">View live page</a>\n'
    )
    h += "            </div>\n"
    h += (
        '            <p class="lp-capture-hint">Use <strong>Hero</strong> or <strong>Careers</strong> '
        "for key sections (Careers includes the Lightcast iframe); <strong>Full page</strong> shows the entire scroll "
        "(scroll inside the frame).</p>\n"
    )
    h += '            <div class="lp-capture-grid">\n'
    h += _lp_device_column("desktop", desktop_frames)
    h += _lp_device_column("mobile", mobile_frames)
    h += "            </div>\n"
    h += "        </section>\n"
    return h


def pct_change(current, prior):
    if prior == 0:
        return None
    return ((current - prior) / prior) * 100


def change_icon(pct):
    if pct is None:
        return '<span class="change neutral">NEW</span>'
    if pct > 5:
        return f'<span class="change up">&#9650; {pct:+.0f}%</span>'
    elif pct < -5:
        return f'<span class="change down">&#9660; {pct:+.0f}%</span>'
    else:
        return f'<span class="change flat">&#9654; {pct:+.0f}%</span>'


def make_anchor(name):
    return name.lower().replace(' ', '-').replace('&', '').replace('/', '-').replace('--', '-')


def fill_monthly_series(months_data: list[dict]) -> list[dict]:
    by_month = {m['month']: m for m in months_data}
    filled = []
    for month in MONTHLY_DETAIL_MONTHS:
        if month in by_month:
            filled.append(by_month[month])
        else:
            filled.append({
                'month': month,
                'leads': 0,
                'apps_started': 0,
                'apps_submitted': 0,
                'decisions': 0,
                'new_enrollments': 0,
            })
    return filled


def enrollment_view(mig: dict | None) -> dict | None:
    if not mig:
        return None
    if 'enrollment_view' in mig:
        return mig.get('enrollment_view')
    if mig.get('enrollments_in') is not None:
        return mig
    return None


def fmt_net_cell(mig: dict | None) -> tuple[str, str]:
    ev = enrollment_view(mig)
    if not ev or ev.get('enrollments_in', 0) == 0:
        return ('—', '—')
    net = ev.get('net_migration', 0)
    sign = '+' if net > 0 else ''
    net_str = f'{sign}{net:,}'
    pct_enr = ev.get('net_pct_enrollments')
    pct_base = ev.get('net_pct_same_path_base')
    if pct_enr is not None and pct_base is not None:
        pct_str = f'{sign}{pct_enr:.1f}% / {sign}{pct_base:.1f}%'
    elif pct_enr is not None:
        pct_str = f'{sign}{pct_enr:.1f}%'
    else:
        pct_str = '—'
    return (net_str, pct_str)


def _flow_anchor_badge(program_name: str) -> str:
    return f'<span class="flow-anchor">{program_name}</span>'


def render_flow_read_hint(program_name: str) -> str:
    anchor = _flow_anchor_badge(program_name)
    return (
        '<p class="flow-read-hint">'
        f'Each row pairs <strong>where the student inquired</strong> with '
        f'<strong>where they ultimately enrolled</strong>. This page is anchored on '
        f'{anchor} — read down for same-program matches, transfers in, and transfers out.'
        '</p>\n'
    )


def render_flow_kpi_band(ev: dict, lv: dict | None) -> str:
    enr_in = ev.get('enrollments_in', 0) or 0
    same = ev.get('same_path_enrollments', 0) or 0
    same_pct = round(100 * same / enr_in, 1) if enr_in else 0
    gained = ev.get('inflow_from_other', 0) or 0
    lost = ev.get('outflow_to_other', 0) or 0
    net = ev.get('net_migration', 0) or 0
    sign = '+' if net > 0 else ''
    net_cls = 'net-positive' if net > 0 else 'net-negative' if net < 0 else ''

    h = '<div class="flow-kpi-grid">\n'

    if lv and lv.get('inquiry_leads', 0) > 0:
        h += (
            '<div class="flow-kpi flow-kpi--cohort">\n'
            '<span class="flow-kpi-label">12-month inquiry cohort</span>\n'
            f'<span class="flow-kpi-value">{lv["inquiry_leads"]:,} leads</span>\n'
            f'<span class="flow-kpi-sub">'
            f'{lv["enrollment_rate_pct"]:.2f}% enrolled · '
            f'{lv["final_enrollments"]:,} final · '
            f'{lv["enrolled_in_program"]:,} stayed · '
            f'{lv["enrolled_elsewhere"]:,} elsewhere'
            f'</span>\n</div>\n'
        )

    h += (
        '<div class="flow-kpi flow-kpi--enrolled">\n'
        '<span class="flow-kpi-label">Final enrollments (applied here)</span>\n'
        f'<span class="flow-kpi-value">{enr_in:,}</span>\n'
        f'<span class="flow-kpi-sub">{same:,} same inquiry &amp; program '
        f'({same_pct:.1f}%)</span>\n</div>\n'
        '<div class="flow-kpi flow-kpi--migration">\n'
        '<span class="flow-kpi-label">Program switching (net)</span>\n'
        '<span class="flow-kpi-migration">'
        f'<span class="flow-kpi-in">+{gained:,} in</span>'
        f'<span class="flow-kpi-out">−{lost:,} out</span>'
        f'</span>\n'
        f'<span class="flow-kpi-sub {net_cls}">Net {sign}{net:,}'
    )
    pct_enr = ev.get('net_pct_enrollments')
    pct_base = ev.get('net_pct_same_path_base')
    if pct_enr is not None:
        h += f' · {sign}{pct_enr:.1f}% of enrollments'
        if pct_base is not None:
            h += f' · {sign}{pct_base:.1f}% vs same-path base'
    h += '</span>\n</div>\n</div>\n'
    return h


def render_flow_balance_strip(ev: dict, program_name: str) -> str:
    """Three-node strip: other inquiries → this program → other enrollments."""
    enr_in = ev.get('enrollments_in', 0) or 0
    gained = ev.get('inflow_from_other', 0) or 0
    lost = ev.get('outflow_to_other', 0) or 0
    if enr_in <= 0:
        return ''
    anchor = _flow_anchor_badge(program_name)
    return (
        '<div class="flow-balance" role="img" '
        'aria-label="Inquiry sources, enrollments in program, enrollments elsewhere">\n'
        '<div class="flow-balance-node flow-balance-node--in">'
        f'<span class="flow-balance-num">+{gained:,}</span>'
        '<span class="flow-balance-cap">from other<br>inquiries</span></div>\n'
        '<div class="flow-balance-arrow" aria-hidden="true">→</div>\n'
        f'<div class="flow-balance-node flow-balance-node--anchor">{anchor}'
        f'<span class="flow-balance-num flow-balance-num--main">{enr_in:,}</span>'
        '<span class="flow-balance-cap">enrolled here</span></div>\n'
        '<div class="flow-balance-arrow" aria-hidden="true">→</div>\n'
        '<div class="flow-balance-node flow-balance-node--out">'
        f'<span class="flow-balance-num">−{lost:,}</span>'
        '<span class="flow-balance-cap">to other<br>programs</span></div>\n'
        '</div>\n'
    )


def render_flow_table(
    view: dict,
    title: str,
    footnote: str,
    program_name: str,
    *,
    count_header: str = 'Final enrollments',
) -> str:
    if not view or not view.get('flow_rows'):
        return ''

    anchor = _flow_anchor_badge(program_name)
    h = '<div class="card flow-card">\n'
    h += f'<h4>{title}</h4>\n'
    h += render_flow_read_hint(program_name)
    h += f'<p class="flow-footnote">{footnote}</p>\n'
    h += render_flow_kpi_band(view, view.get('_lead_cohort'))
    h += render_flow_balance_strip(view, program_name)
    h += '<div class="flow-table-wrap">\n'
    h += (
        '<div class="flow-col-labels">'
        '<span>Inquired about</span>'
        '<span class="flow-col-arrow" aria-hidden="true">→ enrolled in →</span>'
        '</div>\n'
    )
    h += (
        '<table class="flow-table"><thead><tr>'
        f'<th>Inquiry program</th><th>{count_header}</th><th>% of enrollments</th>'
        '<th>Enrolled in (applied)</th></tr></thead><tbody>\n'
    )

    section_meta = {
        'in': (
            'flow-section-in',
            '← Transferred in',
            f'Inquired elsewhere · enrolled in {program_name}',
        ),
        'out': (
            'flow-section-out',
            'Transferred out →',
            f'Inquired about {program_name} · enrolled elsewhere',
        ),
    }
    last_section = None
    for row in view.get('flow_rows', []):
        sec = row.get('section', '')
        if sec != last_section and sec in section_meta:
            cls, title_short, title_long = section_meta[sec]
            h += (
                f'<tr class="flow-section-row {cls}"><td colspan="4">'
                f'<span class="flow-section-title">{title_short}</span>'
                f'<span class="flow-section-desc">{title_long}</span>'
                f'</td></tr>\n'
            )
            last_section = sec
        elif sec != last_section:
            last_section = sec

        row_class = 'flow-row-same' if sec == 'same' else f'flow-row-{sec}'
        if row.get('is_other'):
            row_class += ' flow-other'
        inquiry = row['inquiry']
        applied = row['applied']
        if sec == 'same':
            inquiry = f'<strong>{inquiry}</strong>'
            applied = f'<strong>{applied}</strong>'
            row_class += ' flow-row-highlight'
        elif sec == 'in':
            applied = anchor
            inquiry = f'<strong>{inquiry}</strong>'
        elif sec == 'out':
            inquiry = anchor
            applied = (
                f'<strong>{applied}</strong>'
                if not row.get('is_other')
                else applied
            )

        h += (
            f'<tr class="{row_class}"><td>{inquiry}</td>'
            f'<td class="num">{row["count"]:,}</td>'
            f'<td class="num pct">{row["pct"]:.1f}%</td>'
            f'<td>{applied}</td></tr>\n'
        )

    h += '</tbody></table></div></div>\n'
    return h


def render_migration_sections(mig: dict | None, program_name: str = '') -> str:
    if not mig:
        return ''

    html_parts = []
    lv = mig.get('lead_cohort_view')
    ev = enrollment_view(mig)
    if ev and ev.get('enrollments_in', 0) > 0:
        ev_with_cohort = dict(ev)
        if lv:
            ev_with_cohort['_lead_cohort'] = lv

        footnote = (
            'Final enrollment (<code>is_new_enrollment_final</code>), same academic level only. '
            'Undecided inquiry programs roll up to <strong>Undecided</strong>.'
        )
        if lv and lv.get('inquiry_leads', 0) > 0:
            footnote += ' Cohort band uses 12-month inquiry leads for this program.'

        display_name = program_name or mig.get('program_name') or 'this program'
        html_parts.append(
            render_flow_table(
                ev_with_cohort,
                'Program enrollments — inquiry vs applied',
                footnote,
                display_name,
            )
        )

    if not html_parts:
        return ''
    return '<div class="flow-block">\n' + ''.join(html_parts) + '</div>\n'


def render_migration_inquiry_na_card() -> str:
    return (
        '<div class="card flow-card flow-na-card">\n'
        '<h4>Program enrollments — inquiry vs applied</h4>\n'
        '<p class="flow-footnote">Cross-program inquiry → applied mapping is defined '
        'per program, not for a level-wide total.</p>\n'
        '<p class="flow-na-label">N/A at this level</p>\n'
        '</div>\n'
    )


def render_migration_net_na_card() -> str:
    return (
        '<div class="card flow-card flow-na-card">\n'
        '<h4>Enrollment migration (net, all programs)</h4>\n'
        '<p class="flow-footnote">Net inflow/outflow is computed per program from '
        'inquiry-vs-applied paths; it cannot be interpreted as one rolled-up level view.</p>\n'
        '<p class="flow-na-label">N/A at this level</p>\n'
        '</div>\n'
    )


def render_level_migration_block(mig: dict | None) -> str:
    """Level totals: migration views are per-program only."""
    del mig
    return (
        '<div class="flow-block">\n'
        + render_migration_net_na_card()
        + render_migration_inquiry_na_card()
        + "</div>\n"
    )


def render_demographics_section(
    prof: dict | None,
    program_name: str,
    degree_level: str,
    baselines: dict,
    matric_window_label: str,
) -> str:
    if not prof or prof.get('count', 0) == 0:
        return ''

    baseline_key = 'undergraduate' if degree_level == 'Undergraduate' else 'graduate'
    baseline = baselines.get(baseline_key) or baselines.get('all') or {}
    n = prof['count']

    female_pct = pct_from_dist(prof.get('gender', {}), 'Female')
    baseline_female = pct_from_dist(baseline.get('gender', {}), 'Female')
    female_idx = index_vs_baseline(female_pct, baseline_female)

    minority_yes = pct_from_dist(prof.get('minority', {}), 'Yes') or pct_from_dist(
        prof.get('minority', {}), 'Y'
    )
    baseline_minority = pct_from_dist(baseline.get('minority', {}), 'Yes') or pct_from_dist(
        baseline.get('minority', {}), 'Y'
    )
    minority_idx = index_vs_baseline(minority_yes, baseline_minority)

    is_undergrad = degree_level == 'Undergraduate'
    pell_core = prof.get('pell_core_pct') if is_undergrad else None
    pell_core_n = prof.get('pell_core_n') if is_undergrad else None
    mil_funding = prof.get('military_funding_pct')
    mil_lob_n = prof.get('military_lob_n')

    h = '<div class="card demo-card">\n'
    h += '<h4>Enrolled student profile</h4>\n'
    footnote = (
        f'Students matriculated ({matric_window_label}, 12-month window) '
        f'via StudentRevenueMaster / program bridge. '
        f'Indexed highlights compare to <strong>{baseline_key}</strong> enrolled baseline.'
    )
    if is_undergrad:
        footnote += (
            ' Pell % is among Core LOB enrollments; military funding % is among Military LOB. '
            'Transfer credits apply to undergraduate programs only.'
        )
    else:
        footnote += (
            ' Pell is omitted for graduate programs. Military funding % is among Military LOB enrollments.'
        )
    h += f'<p class="flow-footnote">{footnote}</p>\n'
    h += f'<p class="demo-count">{n:,} enrolled students</p>\n'
    h += '<div class="demo-highlights">\n'
    if prof.get('age_median') is not None:
        h += f'<span class="highlight-stat">Median age: <strong>{prof["age_median"]}</strong></span>\n'
    if female_pct is not None:
        idx_note = (
            f' <span class="idx-badge">index {female_idx}</span>' if female_idx else ''
        )
        h += f'<span class="highlight-stat">Female: <strong>{female_pct:.1f}%</strong>{idx_note}</span>\n'
    if minority_yes is not None:
        idx_note = (
            f' <span class="idx-badge">index {minority_idx}</span>'
            if minority_idx
            else ''
        )
        h += f'<span class="highlight-stat">Minority: <strong>{minority_yes:.1f}%</strong>{idx_note}</span>\n'
    if is_undergrad and pell_core is not None:
        n_note = f' (Core, n={pell_core_n:,})' if pell_core_n else ' (Core)'
        h += (
            f'<span class="highlight-stat">% Pell{n_note}: '
            f'<strong>{pell_core:.1f}%</strong></span>\n'
        )
    if mil_funding is not None:
        n_note = f' (Military LOB, n={mil_lob_n:,})' if mil_lob_n else ' (Military LOB)'
        h += (
            f'<span class="highlight-stat">% Military funding{n_note}: '
            f'<strong>{mil_funding:.1f}%</strong></span>\n'
        )
    h += '</div>\n'

    h += '<div class="profile-grid">\n'

    h += '<div class="profile-card"><h5>Gender</h5>'
    h += render_composition_strip(
        display_gender(prof.get('gender', {})),
        colors=GENDER_COLORS,
        aria_label='Gender',
    )
    h += '</div>\n'

    # ── Gender × LOB cross-tab ──────────────────────────────────────────
    gender_by_lob_data = prof.get('gender_by_lob', {})
    if gender_by_lob_data:
        baseline_gbl = baseline.get('gender_by_lob', {})
        lob_order = [l for l in ('Core', 'Military', 'B2B', 'TB') if l in gender_by_lob_data]

        # ── Option A: stacked bar per LOB ──
        h += '<div class="profile-card profile-card--wide"><h5>Gender by line of business</h5>\n'
        h += '<div class="gender-lob-bars">\n'
        for lob in lob_order:
            gdist = gender_by_lob_data[lob]
            female_pct = gdist.get('Female', 0)
            bl_female = baseline_gbl.get(lob, {}).get('Female')
            delta_html = ''
            if bl_female is not None:
                diff = female_pct - bl_female
                sign = '+' if diff >= 0 else ''
                cls = 'lob-delta-up' if diff >= 2 else ('lob-delta-down' if diff <= -2 else 'lob-delta-flat')
                delta_html = f'<span class="lob-delta {cls}">{sign}{diff:.0f}pp vs baseline</span>'
            h += (
                f'<div class="gender-lob-row">'
                f'<div class="gender-lob-lbl">{lob}</div>'
                f'<div class="gender-lob-bar">'
                + render_composition_strip(gdist, colors=GENDER_COLORS, aria_label=f'Gender {lob}')
                + f'</div>'
                f'{delta_html}'
                f'</div>\n'
            )
        h += '</div>\n'  # gender-lob-bars

        # ── Option B: compact female% comparison table ──
        h += '<div class="gender-lob-table-wrap">\n'
        h += '<p class="gender-lob-label-b">% Female by LOB</p>\n'
        h += '<table class="gender-lob-tbl">\n'
        h += '<thead><tr><th>LOB</th><th>% Female</th><th>% Male</th><th>vs Baseline</th></tr></thead>\n<tbody>\n'
        for lob in lob_order:
            gdist = gender_by_lob_data[lob]
            female_pct = gdist.get('Female', 0)
            male_pct = gdist.get('Male', 0)
            bl_female = baseline_gbl.get(lob, {}).get('Female')
            if bl_female is not None:
                diff = female_pct - bl_female
                sign = '+' if diff >= 0 else ''
                cls = 'delta-pos' if diff >= 2 else ('delta-neg' if diff <= -2 else '')
                delta_cell = f'<span class="{cls}">{sign}{diff:.0f}pp</span>'
            else:
                delta_cell = '—'
            bar_w = int(round(female_pct))
            h += (
                f'<tr>'
                f'<td class="lob-name">{lob}</td>'
                f'<td class="lob-pct">'
                f'<div class="lob-mini-bar" style="--w:{bar_w}%;--c:#AB0520">'
                f'<span>{female_pct:.1f}%</span></div></td>'
                f'<td class="lob-pct">{male_pct:.1f}%</td>'
                f'<td class="lob-vs">{delta_cell}</td>'
                f'</tr>\n'
            )
        h += '</tbody></table>\n'
        h += '</div>\n'  # gender-lob-table-wrap
        h += '</div>\n'  # profile-card
    # ── End Gender × LOB ────────────────────────────────────────────────

    h += '<div class="profile-card"><h5>Race / ethnicity</h5>'
    h += render_composition_strip(
        display_race(prof.get('race', {})),
        colors=RACE_COLORS,
        aria_label='Race',
    )
    h += '</div>\n'

    if prof.get('age_under25') is not None:
        h += '<div class="profile-card"><h5>Age at matriculation</h5>'
        h += '<div class="age-distribution">\n'
        for label, key in [
            ('Under 25', 'age_under25'),
            ('25–34', 'age_25to34'),
            ('35–44', 'age_35to44'),
            ('45+', 'age_45plus'),
        ]:
            val = prof.get(key)
            if val is not None:
                h += (
                    f'<div class="age-bucket"><div class="value">{val:.1f}%</div>'
                    f'<div class="label">{label}</div></div>\n'
                )
        h += '</div>\n'
        if prof.get('age_mean') is not None:
            h += (
                f'<p class="demo-age-note">Mean {prof["age_mean"]:.1f}'
                f' | Median {prof.get("age_median", "—")}</p>\n'
            )
        h += '</div>\n'

    h += '<div class="profile-card"><h5>Marital status</h5>'
    h += render_composition_strip(
        display_maritalstatus(prof.get('maritalstatus', {})),
        colors=MARITAL_COLORS,
        aria_label='Marital status',
    )
    h += '</div>\n'

    h += '</div>\n'

    if is_undergrad and prof.get('transferstatus'):
        h += '<div class="profile-card profile-card--wide"><h5>Transfer credits</h5>'
        h += render_composition_strip(
            display_transfer_credits(prof.get('transferstatus', {})),
            colors=TRANSFER_CREDIT_COLORS,
            aria_label='Transfer credits at matriculation',
        )
        h += '</div>\n'

    h += '</div>\n'
    return h


def render_widget_composition_row(
    bar_label: str,
    total: int,
    aria_label: str,
    *,
    dist: dict[str, float] | None = None,
    rows: list[dict] | None = None,
    colors: dict[str, str] | None = None,
) -> str:
    if total <= 0 or (not dist and not rows):
        return ''
    h = f'<div class="widget-comp-row">\n'
    h += (
        f'<div class="widget-comp-head">{bar_label}'
        f'<span class="widget-comp-total">{total:,}</span></div>\n'
    )
    if dist:
        h += render_composition_strip(
            dist, colors=colors or {}, max_items=12, aria_label=aria_label
        )
    else:
        h += render_composition_strip(
            rows=rows, colors=colors or {}, max_items=12, aria_label=aria_label
        )
    h += '</div>\n'
    return h


def render_detail_widgets(pid: str, region_html: str = "") -> str:
    w = detail_widgets.get(pid)
    if not w:
        return ''

    seg = w.get("marketing_segment", {})
    lob = w.get("enrollment_lob", {})
    rollup_lead_rows = seg.get("rollup_leads", [])
    rollup_enr_rows = seg.get("rollup_enrollments", [])
    paid_lead_rows = seg.get("paid_leads_breakdown", [])
    paid_enr_rows = seg.get("paid_enrollment_breakdown", [])
    lob_rows = lob.get("buckets", [])

    if (
        not rollup_lead_rows
        and not paid_lead_rows
        and not lob_rows
        and not region_html
    ):
        return ''

    h = '<div class="detail-widgets">\n'

    if rollup_lead_rows or rollup_enr_rows or paid_lead_rows or paid_enr_rows:
        h += '<div class="card widget-card">\n'
        h += '<h4>Marketing segment mix</h4>\n'
        h += (
            f'<p class="flow-footnote">Share of inquiry leads and final enrollments '
            f'({primary_label}) by marketing rollup (Paid, Navigational, B2B). '
            'Paid details use <code>initial_marketing_segment1</code> among Paid-only volume. '
            'Mapped from <code>mars_segment_legacy</code>; unknown/other excluded.</p>\n'
        )
        if rollup_lead_rows:
            h += render_widget_composition_row(
                "Leads — marketing rollup",
                seg.get("rollup_leads_total", 0),
                "Marketing rollup — leads",
                rows=rollup_lead_rows,
                colors=widget_marketing_rollup_colors,
            )
        if rollup_enr_rows:
            h += render_widget_composition_row(
                "Final enrollments — marketing rollup",
                seg.get("rollup_enrollments_total", 0),
                "Marketing rollup — enrollments",
                rows=rollup_enr_rows,
                colors=widget_marketing_rollup_colors,
            )
        if paid_lead_rows or paid_enr_rows:
            h += '<div class="widget-paid-divider"></div>\n'
            h += '<h5 class="widget-paid-details-title">Paid details</h5>\n'
            h += (
                '<p class="flow-footnote widget-paid-footnote">'
                'Paid-only leads and enrollments by initial marketing segment1 '
                '(Display, Affiliate, Affiliate - Search, Non-Brand Search).</p>\n'
            )
            if paid_lead_rows:
                h += render_widget_composition_row(
                    "Leads — Paid",
                    seg.get("paid_leads_total", 0),
                    "Paid segment1 — leads",
                    rows=paid_lead_rows,
                    colors=widget_segment1_colors,
                )
            if paid_enr_rows:
                h += render_widget_composition_row(
                    "Final enrollments — Paid",
                    seg.get("paid_enrollments_total", 0),
                    "Paid segment1 — enrollments",
                    rows=paid_enr_rows,
                    colors=widget_segment1_colors,
                )
        h += '</div>\n'

    if lob_rows:
        h += '<div class="card widget-card">\n'
        h += '<h4>Enrollments by line of business</h4>\n'
        h += (
            f'<p class="flow-footnote">Share of enrolled students matriculated '
            f'({lob_matric_label}) from StudentRevenueMaster: Core, FTG (full tuition grant), '
            f'TB (tuition benefit), Military.</p>\n'
        )
        lob_dist = display_lineofbusiness(
            {b["label"]: b["pct"] for b in lob_rows}
        )
        h += render_widget_composition_row(
            "Enrolled students",
            lob.get("total", 0),
            "Line of business — enrollments",
            dist=lob_dist,
            colors=LOB_DEMO_COLORS,
        )
        if region_html:
            h += region_html
        h += '</div>\n'

    h += '</div>\n'
    return h


# Split programs into grad / undergrad / undecided
undergrad = [p for p in programs if p['degree_level'] == 'Undergraduate']
graduate = [p for p in programs if p['degree_level'] != 'Undergraduate']
undergrad_enrolling = [p for p in undergrad if not is_undecided_program(p)]
undergrad_undecided = [p for p in undergrad if is_undecided_program(p)]


def matrix_sort_key(program: dict) -> int:
    """Descending final enrollments; level total and undecided rollup are pinned in render_matrix_table."""
    return -(program.get("new_enrollments") or 0)


undergrad_enrolling.sort(key=matrix_sort_key)
graduate.sort(key=matrix_sort_key)

program_by_id = {p["program_id"]: p for p in programs}
ENROLLING_DETAIL_PROGRAM_IDS = frozenset(
    p["program_id"] for p in undergrad_enrolling + graduate
)
ALL_DETAIL_PROGRAM_IDS = (
    ENROLLING_DETAIL_PROGRAM_IDS
    | LEVEL_DETAIL_PROGRAM_IDS
    | frozenset({UNDECIDED_ROLLUP_ID})
)
alignment_by_pid = resolve_alignment_by_program_id(programs, alignment_data)
print(f"Academic alignment mapped: {len(alignment_by_pid)}/{len(programs)} programs")

print(f"Undergraduate (enrolling): {len(undergrad_enrolling)}")
print(f"Undecided: {len(undergrad_undecided)}")
print(f"Graduate: {len(graduate)}")
print(f"Program detail pages: {len(ENROLLING_DETAIL_PROGRAM_IDS)}")

level_links_html = " · ".join(
    f'<a href="#{make_anchor(label)}">{label}</a>'
    for label in (
        LEVEL_DETAIL_LABELS[UNDERGRAD_TOTAL_ID],
        LEVEL_DETAIL_LABELS[GRADUATE_TOTAL_ID],
        UNDECIDED_DETAIL_LABEL,
    )
)

REPORT_TITLE = "UAGC Marketing and Enrollment Details, By Program"

# ========== BUILD HTML ==========
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<title>{REPORT_TITLE}</title>
<style>
:root {{
    --arizona-red: #AB0520;
    --arizona-blue: #0C234B;
    --uagc-red: var(--arizona-red);
    --uagc-dark: var(--arizona-blue);
    --bg: #f4f4f3;
    --card: #ffffff;
    --surface-alt: #f4f4f3;
    --border: #D0D0CE;
    --text: #53565A;
    --muted: #98A4AE;
    --link: #0076A8;
    --highlight-blue: #81D3EB;
    --positive: #007D8A;
    --negative: var(--arizona-red);
    --font-sans: "Montserrat", Calibri, "Segoe UI", system-ui, sans-serif;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: var(--font-sans); background: var(--bg); color: var(--text); line-height: 1.45; font-size: 0.875rem; }}
.container {{ max-width: 100%; margin: 0 auto; padding: 1.25rem 1.25rem 2rem; }}
h1 {{ color: var(--uagc-dark); font-size: 1.5rem; font-weight: 700; margin-bottom: 0.2rem; letter-spacing: -0.01em; }}
.subtitle {{ color: var(--muted); margin-bottom: 0.5rem; font-size: 0.875rem; }}
.sample-note {{ font-size: 0.8rem; color: var(--text); margin-bottom: 1.25rem; line-height: 1.4; max-width: 52rem; }}
.sample-note a {{ color: var(--link); text-decoration: none; font-weight: 500; }}
.sample-note a:hover {{ text-decoration: underline; }}
.link-muted {{ color: var(--muted); font-size: 0.72rem; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 6px; padding: 1rem 1.15rem; margin-bottom: 1.25rem; }}
.card h2 {{ color: var(--uagc-dark); margin-bottom: 0.65rem; font-size: 1.1rem; font-weight: 700; }}

/* Tabs */
.tabs {{ display: flex; gap: 0; margin-bottom: 0; }}
.tab {{ padding: 0.55rem 1.1rem; cursor: pointer; border: 1px solid var(--border); border-bottom: none; border-radius: 6px 6px 0 0; background: var(--surface-alt); color: var(--muted); font-weight: 600; font-size: 0.8rem; }}
.tab.active {{ background: var(--card); color: var(--uagc-dark); border-bottom: 1px solid var(--card); margin-bottom: -1px; z-index: 1; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.tab-panel {{ border: 1px solid var(--border); border-radius: 0 6px 6px 6px; background: var(--card); padding: 0.65rem 0.75rem; }}

/* Organization navigation tab */
.org-nav-intro {{ margin-bottom: 0.65rem; }}
.org-nav-jumps {{
  font-size: 0.78rem; line-height: 1.5; margin-bottom: 0.85rem;
  padding: 0.5rem 0.65rem; background: var(--surface-alt); border-radius: 4px;
}}
.org-nav-jumps-label {{ color: var(--muted); font-weight: 600; }}
.org-nav-jumps a {{ color: var(--link); text-decoration: none; font-weight: 500; }}
.org-nav-jumps a:hover {{ text-decoration: underline; }}
.org-nav-tree {{ font-size: 0.82rem; line-height: 1.45; }}
.org-nav-tree details {{ margin: 0 0 0.35rem 0.25rem; }}
.org-nav-dean > summary {{
  font-weight: 700; color: var(--uagc-dark); font-size: 0.95rem;
  cursor: pointer; padding: 0.35rem 0.25rem;
}}
.org-nav-ad > summary {{
  font-weight: 600; color: var(--text); font-size: 0.88rem;
  cursor: pointer; padding: 0.25rem 0.25rem 0.25rem 0.75rem;
}}
.org-nav-count {{ font-weight: 500; color: var(--muted); font-size: 0.78em; }}
.org-nav-dh-block {{ margin: 0.2rem 0 0.5rem 1.5rem; }}
.org-nav-dh {{
  font-weight: 600; color: var(--uagc-dark); font-size: 0.8rem;
  margin: 0.35rem 0 0.2rem; padding-left: 0.5rem;
  border-left: 3px solid var(--uagc-red);
}}
.org-nav-programs {{
  list-style: none; margin: 0 0 0.35rem; padding: 0 0 0 1rem;
}}
.org-nav-programs li {{ margin: 0.12rem 0; }}
.org-nav-programs a {{ color: var(--link); text-decoration: none; }}
.org-nav-programs a:hover {{ text-decoration: underline; }}
.org-nav-unmapped {{ margin-top: 1rem; }}
.org-nav-unmapped > summary {{ font-weight: 600; color: var(--muted); cursor: pointer; }}
.org-nav-empty {{ color: var(--muted); font-size: 0.85rem; }}

/* Tables */
table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; line-height: 1.3; }}
th {{ background: var(--uagc-dark); color: white; padding: 0.45rem 0.55rem; text-align: left; position: sticky; top: 0; z-index: 2; white-space: nowrap; font-weight: 600; font-size: 0.72rem; }}
th:nth-child(n+4) {{ text-align: right; }}
th:nth-child(1), th:nth-child(2), th:nth-child(3) {{ text-align: left; }}
td {{ padding: 0.32rem 0.55rem; border-bottom: 1px solid var(--border); }}
td:nth-child(n+4) {{ text-align: right; font-variant-numeric: tabular-nums; }}
td:nth-child(1), td:nth-child(2), td:nth-child(3) {{ text-align: left; }}
tr:hover {{ background: rgba(0, 118, 168, 0.06); }}
.link-cell {{ white-space: nowrap; font-size: 0.58rem; }}
.link-cell a {{ color: var(--link); text-decoration: none; font-size: 0.58rem; margin-right: 0.35rem; }}
.link-cell a:hover {{ text-decoration: underline; }}

/* KPIs */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; }}
.kpi {{ background: var(--card); color: var(--uagc-dark); border: 1px solid var(--border); border-top: 3px solid var(--uagc-red); border-radius: 4px; padding: 0.75rem 0.5rem; text-align: center; }}
.kpi .value {{ font-size: 1.35rem; font-weight: 700; line-height: 1.1; }}
.kpi .label {{ font-size: 0.65rem; font-weight: 600; color: var(--muted); margin-top: 0.15rem; }}
.kpi .change {{ display: inline-block; margin-top: 0.25rem; font-size: 0.72rem; padding: 0.1rem 0.35rem; border-radius: 4px; font-weight: 600; }}
.change.up {{ background: rgba(0, 125, 138, 0.12); color: var(--positive); }}
.change.down {{ background: rgba(171, 5, 32, 0.1); color: var(--negative); }}
.change.flat {{ background: var(--surface-alt); color: var(--muted); }}
.change.neutral {{ background: var(--surface-alt); color: var(--muted); }}

/* Matrix vs prior */
.chg-prior {{ display: inline-block; padding: 0.08rem 0.32rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; color: var(--uagc-dark); }}
.chg-prior.chg-up {{ background: rgba(0, 125, 138, 0.12); color: var(--positive); }}
.chg-prior.chg-down {{ background: rgba(171, 5, 32, 0.1); color: var(--negative); }}
.chg-prior.chg-flat {{ background: var(--surface-alt); color: var(--muted); }}
.chg-prior.chg-new {{ background: var(--surface-alt); color: var(--muted); }}

/* Summary matrix — grouped bands, scan-friendly rhythm */
.matrix-legend {{
  font-size: 0.68rem; color: var(--muted); margin: 0 0 0.5rem; line-height: 1.45;
  display: flex; flex-wrap: wrap; gap: 0.35rem 1rem;
}}
.matrix-legend strong {{ color: var(--uagc-dark); font-weight: 600; }}
.matrix-legend-top5::before {{
  content: ""; display: inline-block; width: 0.7rem; height: 0.7rem;
  border: 1px solid var(--link); background: rgba(0, 118, 168, 0.08);
  margin-right: 0.3rem; vertical-align: -0.12em;
}}
.matrix-wrap {{
  overflow-x: visible;
  border: 1px solid var(--border); border-radius: 4px; background: var(--card);
}}
.matrix-table {{
  width: 100%; min-width: 0; table-layout: fixed;
  font-size: 0.6rem; line-height: 1.3; border-collapse: separate; border-spacing: 0;
}}
.matrix-table .matrix-band-row th {{
  background: var(--uagc-dark); color: #fff; font-size: 0.6rem; font-weight: 600;
  padding: 0.4rem 0.5rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.12);
  position: sticky; top: 0; z-index: 5; white-space: nowrap;
}}
.matrix-table .matrix-cols-row th {{
  background: #152a4a; color: #fff; font-size: 0.56rem; font-weight: 600;
  padding: 0.28rem 0.2rem; text-align: right; white-space: normal;
  line-height: 1.15; vertical-align: bottom; hyphens: auto;
  position: sticky; top: 1.65rem; z-index: 4;
}}
.matrix-table .matrix-cols-row th:nth-child(1),
.matrix-table .matrix-cols-row th:nth-child(2),
.matrix-table .matrix-cols-row th:nth-child(3),
.matrix-table .matrix-cols-row th:nth-child(4) {{ text-align: left; }}
.matrix-table td {{
  padding: 0.26rem 0.22rem; border-bottom: 1px solid var(--border);
  text-align: right; font-variant-numeric: tabular-nums;
  overflow: hidden; text-overflow: ellipsis;
}}
.matrix-table td:nth-child(1),
.matrix-table td:nth-child(2),
.matrix-table td:nth-child(3),
.matrix-table td:nth-child(4) {{ text-align: left; }}
.matrix-table tbody tr.matrix-row-data {{ background: var(--card); }}
.matrix-table tbody tr.matrix-row-data:nth-child(2n) {{ background: var(--surface-alt); }}
.matrix-table tbody tr.matrix-row-data:hover {{ background: rgba(0, 118, 168, 0.07); }}
.matrix-table td.matrix-program {{
  font-weight: 600; color: var(--uagc-dark);
  text-align: left; white-space: nowrap;
}}
.matrix-table td:nth-child(3) {{ color: var(--muted); font-size: 0.62rem; white-space: nowrap; }}
.matrix-table td:nth-child(8),
.matrix-table td:nth-child(9) {{ color: var(--muted); font-size: 0.64rem; }}
.matrix-table td.matrix-top5 {{
  color: var(--uagc-dark); font-weight: 600;
  border: 1px solid var(--link) !important; background: rgba(0, 118, 168, 0.08);
}}
.matrix-table th.matrix-col-sep,
.matrix-table td.matrix-col-sep {{
  border-left: 2px solid var(--muted); padding-left: 0.5rem;
}}
.matrix-table .matrix-band--lob {{ background: #1a3358; }}
.matrix-row-total {{ background: #dce4ec !important; font-weight: 700; }}
.matrix-row-total td {{
  border-top: 2px solid var(--uagc-dark); border-bottom: 2px solid var(--uagc-dark);
  color: var(--uagc-dark);
}}
.matrix-row-undecided {{ background: var(--surface-alt) !important; font-weight: 600; font-style: italic; }}
.matrix-row-undecided td {{ border-top: 2px solid var(--border); }}

/* Charts */
.chart-container {{ margin: 1.5rem 0; }}
.bar-chart {{ display: flex; align-items: flex-end; gap: 3px; height: 150px; padding: 0 0 2rem 0; border-bottom: 1px solid var(--border); position: relative; }}
.bar-group {{ flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; height: 100%; justify-content: flex-end; }}
.bar {{ width: 70%; border-radius: 3px 3px 0 0; background: var(--uagc-red); min-height: 2px; transition: all 0.2s; }}
.bar:hover {{ opacity: 0.8; }}
.bar-label {{ position: absolute; bottom: -1.8rem; font-size: 0.65rem; color: var(--muted); white-space: nowrap; }}
.bar-value {{ position: absolute; top: -1.2rem; font-size: 0.6rem; color: var(--text); font-weight: 600; }}

/* Funnel */
.funnel {{ display: flex; align-items: center; gap: 0; margin: 1rem 0; flex-wrap: wrap; }}
.funnel-stage {{ text-align: center; padding: 0.8rem 1.2rem; position: relative; flex: 1; min-width: 120px; }}
.funnel-stage .stage-value {{ font-size: 1.4rem; font-weight: 700; color: var(--uagc-dark); }}
.funnel-stage .stage-label {{ font-size: 0.7rem; color: var(--muted); text-transform: uppercase; }}
.funnel-stage .stage-pct {{ font-size: 0.75rem; color: var(--uagc-red); font-weight: 600; margin-top: 0.2rem; }}
.funnel-arrow {{ color: var(--border); font-size: 1.5rem; }}

/* Detail */
.detail-section {{ page-break-before: always; margin-top: 1.75rem; padding-top: 1rem; border-top: 2px solid var(--uagc-red); }}
.detail-section--level-total {{
  margin-top: 2.25rem; padding-top: 1.35rem; border-top: 3px solid var(--uagc-dark);
}}
.detail-section--level-total .detail-header h3 {{
  font-size: 1.65rem; letter-spacing: -0.02em; line-height: 1.15; margin-bottom: 0.35rem;
}}
.detail-section--level-total .detail-header .meta {{ font-size: 0.85rem; }}
.detail-section .card {{ padding: 0.875rem 1rem; margin-bottom: 0.75rem; }}
.detail-header {{ margin-bottom: 0.75rem; }}
.detail-header h3 {{ font-size: 1.2rem; color: var(--uagc-dark); margin-bottom: 0.2rem; font-weight: 700; }}
.detail-header .meta {{ color: var(--muted); font-size: 0.8rem; }}
.detail-header .meta a {{ color: var(--link); text-decoration: none; }}
.detail-header .meta-ids {{ font-family: ui-monospace, Consolas, monospace; font-size: 0.72rem; }}
.alignment-card {{ margin-bottom: 0.75rem; padding: 0.75rem 1rem; }}
.alignment-card h4 {{ font-size: 0.95rem; color: var(--uagc-dark); margin-bottom: 0.45rem; }}
.alignment-apl {{ font-size: 0.72rem; color: var(--muted); margin: 0 0 0.5rem; }}
.alignment-dl {{
  display: grid; grid-template-columns: minmax(7rem, 10rem) minmax(0, 1fr);
  gap: 0.25rem 1rem; margin: 0; font-size: 0.8rem; line-height: 1.4;
}}
.alignment-dl dt {{ color: var(--muted); font-weight: 600; margin: 0; }}
.alignment-dl dd {{ margin: 0; color: var(--text); }}
.alignment-code {{ color: var(--muted); font-size: 0.75em; font-weight: 500; }}
.detail-section--undecided .detail-header h3 {{ font-size: 1.35rem; }}
.undecided-components {{ width: 100%; border-collapse: collapse; font-size: 0.72rem; margin-top: 0.35rem; }}
.undecided-components th, .undecided-components td {{
  border: 1px solid var(--border); padding: 0.28rem 0.4rem; text-align: left;
}}
.undecided-components th {{ background: var(--surface-alt); color: var(--uagc-dark); font-weight: 600; }}
.undecided-components td.mono {{ font-family: ui-monospace, Consolas, monospace; font-size: 0.68rem; }}

/* Screenshots */
/* Landing page captures — scrollable viewport + section nav */
.lp-capture {{ margin: 0.75rem 0 1rem; }}
.lp-capture-header {{ display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between; gap: 0.5rem 1rem; margin-bottom: 0.35rem; }}
.lp-capture-header h4 {{ color: var(--uagc-dark); font-size: 0.95rem; font-weight: 700; margin: 0; }}
.lp-live-link {{ font-size: 0.78rem; font-weight: 600; color: var(--link); text-decoration: none; }}
.lp-live-link:hover {{ text-decoration: underline; }}
.lp-capture-hint {{ font-size: 0.72rem; color: var(--muted); margin: 0 0 0.6rem; max-width: 42rem; line-height: 1.4; }}
.lp-capture-grid {{
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, 34%);
  gap: 1rem; align-items: start;
}}
.lp-device {{ border: 1px solid var(--border); border-radius: 4px; background: var(--card); overflow: hidden; }}
.lp-device--desktop {{ min-width: 0; }}
.lp-device-head {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.35rem 0.5rem; padding: 0.5rem 0.65rem; border-bottom: 1px solid var(--border); background: var(--surface-alt); }}
.lp-device-name {{ font-size: 0.75rem; font-weight: 700; color: var(--uagc-dark); }}
.lp-nav {{ display: flex; flex-wrap: wrap; gap: 0.15rem; }}
.lp-nav-btn {{ appearance: none; border: none; background: transparent; font-family: inherit; font-size: 0.68rem; font-weight: 600; color: var(--muted); padding: 0.2rem 0.45rem; border-radius: 2px; cursor: pointer; }}
.lp-nav-btn:hover {{ color: var(--uagc-dark); }}
.lp-nav-btn.is-active {{ color: var(--uagc-dark); background: var(--card); border-bottom: 2px solid var(--uagc-red); margin-bottom: -2px; }}
.lp-viewport {{
  overflow-y: scroll; overflow-x: auto; background: #fff;
  scrollbar-gutter: stable;
}}
.lp-viewport--slice {{ max-height: min(72vh, 36rem); }}
.lp-device--desktop .lp-viewport--slice {{ max-height: min(78vh, 40rem); }}
.lp-viewport--full {{ max-height: min(88vh, 52rem); }}
.lp-shot {{ width: 100%; min-width: 100%; height: auto; display: block; vertical-align: top; }}
.screenshot-empty {{ background: var(--surface-alt); border: 1px dashed var(--border); border-radius: 4px; padding: 0.75rem 1rem; margin: 0.65rem 0; font-size: 0.78rem; color: var(--text); }}
.screenshot-empty pre {{ margin-top: 0.4rem; font-size: 0.7rem; background: var(--card); padding: 0.4rem; border-radius: 4px; overflow-x: auto; }}
.sankey-card {{ margin: 0.65rem 0; }}
.sankey-host {{ width: 100%; min-height: 300px; }}
.prose-card {{ margin: 0.65rem 0 0.85rem; background: var(--surface-alt); border-left: 3px solid var(--uagc-red); }}
.prose-card h4 {{ color: var(--uagc-dark); margin-bottom: 0.45rem; font-size: 0.95rem; }}
.prose-card p {{ font-size: 0.8rem; line-height: 1.45; color: var(--text); margin-bottom: 0.4rem; }}
.prose-card p:last-child {{ margin-bottom: 0; }}
.region-card {{ margin: 1rem 0 1.5rem; }}
.us-map-stage {{ position: relative; width: 50%; max-width: 50%; margin: 0.5rem 0 0 0; aspect-ratio: 1000 / 520; }}
.us-map-stage--compact {{ width: 78%; max-width: 22rem; margin-left: auto; margin-right: auto; }}
.us-map-sketch {{ width: 100%; height: 100%; display: block; }}
.us-map-region {{ stroke: var(--uagc-dark); stroke-width: 1.75; stroke-linejoin: round; stroke-linecap: round; }}
.us-map-region--active {{ stroke-width: 2; }}
.us-map-region--muted {{ stroke: var(--muted); stroke-width: 1; opacity: 0.55; }}
.us-map-outline, .us-map-lakes {{ pointer-events: none; }}
@media (max-width: 720px) {{
  .us-map-stage {{ width: 100%; max-width: 100%; }}
}}
.us-map-pin {{
  position: absolute; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center; gap: 0.1rem;
  padding: 0.35rem 0.5rem; background: rgba(255,255,255,0.94);
  border: 1px solid var(--border); border-radius: 4px;
  font-size: 0.65rem;
  line-height: 1.2; min-width: 4.5rem; text-align: center; z-index: 1;
}}
.us-map-pin-name {{ font-weight: 600; color: var(--uagc-dark); font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.03em; }}
.us-map-pin-pct {{ font-weight: 700; font-size: 0.82rem; color: var(--uagc-dark); }}
.us-map-pin .idx-badge {{ margin-left: 0; margin-top: 0.15rem; }}
@media (max-width: 520px) {{
  .us-map-pin {{ font-size: 0.6rem; padding: 0.25rem 0.35rem; min-width: 3.75rem; }}
  .us-map-pin-pct {{ font-size: 0.72rem; }}
}}
.undecided-block {{ border-top: 4px solid var(--muted); margin-top: 2rem; padding-top: 1rem; }}
.undecided-block > h2 {{ color: var(--uagc-dark); margin-bottom: 1.5rem; }}
.undecided-block .detail-section {{ page-break-before: avoid; border-top: 1px solid var(--border); margin-top: 1rem; padding-top: 1.5rem; }}
.undecided-block.detail-section {{ page-break-before: always; }}

/* Monthly volume chart + table — full content width, ~40% chart / ~60% table */
.monthly-trend {{ margin: 0.75rem 0; width: 100%; }}
.monthly-trend h4 {{ font-size: 0.95rem; margin-bottom: 0.5rem; }}
.monthly-trend-body {{
  display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
  gap: 1rem 1.75rem; align-items: start; width: 100%;
}}
.monthly-chart-panel {{ width: 100%; margin: 0; min-width: 0; }}
.monthly-combo-chart {{ width: 100%; height: auto; display: block; }}
.monthly-grid-line {{ stroke: var(--border); stroke-width: 1; }}
.monthly-y-label {{ font-size: 9px; fill: var(--muted); font-family: var(--font-sans); }}
.monthly-axis-title {{ font-size: 8px; fill: var(--muted); font-weight: 600; font-family: var(--font-sans); }}
.monthly-x-label {{ font-size: 8px; fill: var(--text); font-family: var(--font-sans); }}
.monthly-bar {{ fill: rgba(171, 5, 32, 0.45); stroke: rgba(171, 5, 32, 0.85); stroke-width: 1; }}
.monthly-trend-line {{
  fill: none; stroke: var(--uagc-dark); stroke-width: 2.5;
  stroke-linejoin: round; stroke-linecap: round;
}}
.monthly-trend-dot {{ fill: var(--uagc-dark); }}
.monthly-chart-legend {{
  display: flex; flex-direction: column; gap: 0.2rem;
  font-size: 0.68rem; color: var(--muted); margin-top: 0.35rem;
}}
.monthly-legend-bar::before {{
  content: ""; display: inline-block; width: 0.55rem; height: 0.55rem;
  background: rgba(171, 5, 32, 0.5); border: 1px solid rgba(171, 5, 32, 0.85);
  margin-right: 0.35rem; vertical-align: -0.08em;
}}
.monthly-legend-line::before {{
  content: ""; display: inline-block; width: 0.85rem; height: 0;
  border-top: 2px solid var(--uagc-dark); margin-right: 0.35rem; vertical-align: 0.2em;
}}
.trend-table-wrap {{ overflow-x: auto; margin-top: 0; min-width: 0; }}
.monthly-trend .trend-table-wrap {{ width: 100%; }}
.trend-table {{
  width: max-content; max-width: 100%; border-collapse: collapse;
  font-size: 0.68rem; line-height: 1.35;
}}
.monthly-trend .trend-table {{
  width: 100%; max-width: none; font-size: 0.72rem;
}}
.monthly-trend .trend-table th {{ font-size: 0.68rem; padding: 0.35rem 0.65rem; }}
.monthly-trend .trend-table td {{ padding: 0.28rem 0.65rem; }}
.trend-table th {{
  background: var(--uagc-dark); color: #fff; font-size: 0.62rem;
  padding: 0.3rem 0.5rem; text-align: right; white-space: nowrap;
}}
.trend-table th:first-child {{ text-align: left; }}
.trend-table td {{
  padding: 0.22rem 0.5rem; border-bottom: 1px solid var(--border);
  text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;
}}
.trend-table td:first-child {{ text-align: left; color: var(--uagc-dark); font-weight: 500; }}
.trend-table tbody tr:nth-child(even) {{ background: var(--surface-alt); }}

/* Program flow migration */
.flow-block {{ margin: 0.65rem 0 0.85rem; }}
.flow-card {{ margin: 0 0 0.65rem; }}
.flow-card:last-child {{ margin-bottom: 0; }}
.flow-card h4 {{ color: var(--uagc-dark); margin-bottom: 0.35rem; font-size: 0.95rem; }}
.flow-read-hint {{
  font-size: 0.78rem; color: var(--text); line-height: 1.45; margin: 0 0 0.5rem;
  max-width: 52rem;
}}
.flow-footnote {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 0.55rem; }}
.flow-anchor {{
  display: inline; font-weight: 700; color: var(--uagc-dark);
  border-bottom: 2px solid var(--uagc-red); padding-bottom: 1px;
}}
.flow-kpi-grid {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: 0.5rem;
  margin-bottom: 0.65rem;
}}
.flow-kpi {{
  padding: 0.5rem 0.65rem; border: 1px solid var(--border); border-radius: 4px;
  background: var(--surface-alt);
}}
.flow-kpi-label {{
  display: block; font-size: 0.62rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.04em; color: var(--muted); margin-bottom: 0.2rem;
}}
.flow-kpi-value {{ display: block; font-size: 1rem; font-weight: 700; color: var(--uagc-dark); }}
.flow-kpi-sub {{ display: block; font-size: 0.68rem; color: var(--text); margin-top: 0.15rem; line-height: 1.35; }}
.flow-kpi-migration {{ display: flex; gap: 0.65rem; font-size: 0.85rem; font-weight: 600; margin: 0.1rem 0; }}
.flow-kpi-in {{ color: var(--positive); }}
.flow-kpi-out {{ color: var(--negative); }}
.flow-balance {{
  display: flex; align-items: center; justify-content: center; gap: 0.35rem 0.5rem;
  margin-bottom: 0.75rem; padding: 0.55rem 0.5rem;
  border: 1px solid var(--border); border-radius: 4px; background: var(--card);
  flex-wrap: wrap;
}}
.flow-balance-node {{
  text-align: center; min-width: 5.5rem; padding: 0.25rem 0.35rem;
}}
.flow-balance-node--anchor {{
  border: 1px solid var(--uagc-dark); border-radius: 4px; padding: 0.35rem 0.5rem;
  background: var(--surface-alt); min-width: 8rem;
}}
.flow-balance-num {{ display: block; font-size: 0.9rem; font-weight: 700; color: var(--uagc-dark); }}
.flow-balance-num--main {{ font-size: 1.05rem; }}
.flow-balance-cap {{ display: block; font-size: 0.62rem; color: var(--muted); line-height: 1.25; margin-top: 0.1rem; }}
.flow-balance-arrow {{ font-size: 1rem; color: var(--muted); font-weight: 600; padding: 0 0.15rem; }}
.flow-col-labels {{
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 0.68rem; font-weight: 600; color: var(--muted); margin-bottom: 0.25rem;
  padding: 0 0.1rem;
}}
.flow-col-arrow {{ color: var(--uagc-dark); }}
.flow-table-wrap {{ margin-top: 0.15rem; }}
.flow-table {{ font-size: 0.78rem; width: 100%; }}
.flow-table th {{ background: var(--uagc-dark); font-size: 0.72rem; }}
.flow-table th:nth-child(2), .flow-table th:nth-child(3) {{ text-align: right; }}
.flow-table td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.flow-table td.pct {{ color: var(--muted); font-size: 0.72rem; }}
.flow-section-row td {{
  background: var(--surface-alt); padding: 0.4rem 0.55rem; border-top: 1px solid var(--border);
}}
.flow-section-in td {{ border-left: 3px solid var(--link); }}
.flow-section-out td {{ border-left: 3px solid var(--uagc-red); }}
.flow-section-title {{
  display: block; font-weight: 700; font-size: 0.72rem; color: var(--uagc-dark);
}}
.flow-section-desc {{
  display: block; font-weight: 500; font-size: 0.66rem; color: var(--muted); margin-top: 0.1rem;
}}
.flow-row-highlight td {{ background: var(--surface-alt); border-top: 2px solid var(--uagc-dark); }}
.flow-row-in td:first-child {{ padding-left: 0.75rem; }}
.flow-row-out td:last-child {{ font-weight: 500; }}
.flow-other td {{ font-style: italic; color: var(--muted); }}
.flow-summary {{ display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.75rem; margin-bottom: 0.5rem; padding: 0.45rem 0.65rem; background: var(--surface-alt); border-radius: 4px; border: 1px solid var(--border); }}
.flow-summary .flow-net {{ color: var(--uagc-dark); font-weight: 600; }}
.net-positive {{ color: var(--positive); font-weight: 600; }}
.net-negative {{ color: var(--negative); font-weight: 600; }}

/* Enrolled student demographics */
.demo-card {{ margin: 0.65rem 0 0.85rem; }}
.demo-card h4 {{ color: var(--uagc-dark); margin-bottom: 0.25rem; font-size: 0.95rem; }}
.demo-count {{ font-size: 0.85rem; color: var(--uagc-dark); font-weight: 600; margin-bottom: 0.45rem; }}
.demo-highlights {{ display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.65rem; }}
.highlight-stat {{ display: inline-flex; align-items: center; gap: 0.2rem; background: var(--surface-alt); padding: 0.28rem 0.55rem; border-radius: 4px; font-size: 0.75rem; border: 1px solid var(--border); }}
.highlight-stat strong {{ color: var(--uagc-dark); }}
.idx-badge {{ font-size: 0.62rem; background: var(--uagc-dark); color: white; padding: 0.08rem 0.35rem; border-radius: 4px; margin-left: 0.12rem; }}
.profile-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem; }}
.profile-card {{ background: var(--card); border-radius: 4px; padding: 0.65rem 0.75rem; border: 1px solid var(--border); }}
.profile-grid .profile-card--wide {{ grid-column: 1 / -1; }}
.demo-card > .profile-card--wide {{ margin-top: 0.65rem; }}
.profile-card--wide .comp-bar {{ height: 32px; }}
.profile-card h5 {{ font-size: 0.68rem; font-weight: 600; color: var(--muted); margin-bottom: 0.45rem; }}
.comp-strip {{ margin-top: 0.1rem; }}
.comp-bar {{ display: flex; width: 100%; height: 28px; border-radius: 4px; overflow: hidden; border: 1px solid var(--border); }}
.comp-seg {{ display: flex; align-items: center; justify-content: center; min-width: 1.75rem; overflow: hidden; }}
.comp-seg--narrow {{ min-width: 2.35rem; }}
.comp-seg-in {{ display: inline-flex; align-items: center; justify-content: center; gap: 0.2rem; font-size: 0.6rem; font-weight: 700; line-height: 1.1; text-align: center; padding: 0 2px; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }}
.comp-seg--narrow .comp-seg-in {{ flex-direction: column; gap: 0; font-size: 0.52rem; line-height: 1.05; white-space: normal; }}
.comp-seg-in .comp-lbl {{ display: block; }}
.comp-seg-in .comp-pct {{ display: block; font-size: 0.5rem; font-weight: 600; opacity: 0.95; }}
.age-distribution {{ display: flex; gap: 0.4rem; }}
.age-bucket {{ flex: 1; text-align: center; padding: 0.35rem; background: var(--surface-alt); border-radius: 4px; border: 1px solid var(--border); }}
.age-bucket .value {{ font-size: 1rem; font-weight: 700; color: var(--uagc-dark); }}
.age-bucket .label {{ font-size: 0.62rem; color: var(--muted); margin-top: 0.15rem; }}
.demo-age-note {{ margin-top: 0.5rem; font-size: 0.72rem; color: var(--muted); }}
.demo-empty {{ font-size: 0.75rem; color: var(--muted); }}

/* Gender × LOB — Option A: stacked bars */
.gender-lob-bars {{ display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.9rem; }}
.gender-lob-row {{ display: grid; grid-template-columns: 3.5rem 1fr auto; align-items: center; gap: 0.5rem; }}
.gender-lob-lbl {{ font-size: 0.68rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; text-align: right; }}
.gender-lob-bar .comp-strip {{ margin: 0; }}
.gender-lob-bar .comp-bar {{ height: 22px; }}
.lob-delta {{ font-size: 0.62rem; font-weight: 600; white-space: nowrap; }}
.lob-delta-up {{ color: #007D8A; }}
.lob-delta-down {{ color: var(--arizona-red); }}
.lob-delta-flat {{ color: var(--muted); }}

/* Gender × LOB — Option B: compact table */
.gender-lob-table-wrap {{ border-top: 1px solid var(--border); padding-top: 0.65rem; }}
.gender-lob-label-b {{ font-size: 0.62rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.4rem; }}
.gender-lob-tbl {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; }}
.gender-lob-tbl th {{ font-size: 0.62rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; padding: 0.2rem 0.5rem; border-bottom: 1px solid var(--border); text-align: left; }}
.gender-lob-tbl td {{ padding: 0.3rem 0.5rem; border-bottom: 1px solid var(--lgray,#f0f0f0); vertical-align: middle; }}
.gender-lob-tbl .lob-name {{ font-weight: 700; color: var(--uagc-dark); width: 3.5rem; }}
.gender-lob-tbl .lob-pct {{ text-align: right; font-variant-numeric: tabular-nums; }}
.gender-lob-tbl .lob-vs {{ text-align: right; font-variant-numeric: tabular-nums; }}
.lob-mini-bar {{ position: relative; background: #f0f0f0; border-radius: 2px; height: 18px; min-width: 60px; display: flex; align-items: center; }}
.lob-mini-bar::before {{ content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: var(--w); background: var(--c); border-radius: 2px; opacity: 0.85; }}
.lob-mini-bar span {{ position: relative; z-index: 1; font-size: 0.72rem; font-weight: 700; color: #fff; padding: 0 0.3rem; }}
.delta-pos {{ color: #007D8A; font-weight: 700; }}
.delta-neg {{ color: var(--arizona-red); font-weight: 700; }}

/* Detail widgets: segment + LOB */
.detail-widgets {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.65rem; margin: 0.65rem 0 0.85rem; }}
.widget-geo-embed {{ margin-top: 0.65rem; padding-top: 0.55rem; border-top: 1px solid var(--border); text-align: center; }}
.widget-geo-embed h5 {{ font-size: 0.78rem; font-weight: 700; color: var(--uagc-dark); margin: 0 0 0.25rem; text-align: left; }}
.widget-geo-embed .flow-footnote {{ margin-bottom: 0.35rem; text-align: left; }}
.widget-geo-embed .us-map-stage {{ margin-top: 0.25rem; }}
.widget-geo-embed .us-map-pin {{ font-size: 0.55rem; padding: 0.18rem 0.28rem; min-width: 3.2rem; }}
.widget-geo-embed .us-map-pin-pct {{ font-size: 0.65rem; }}
.widget-card {{ margin: 0; }}
.widget-card h4 {{ color: var(--uagc-dark); margin-bottom: 0.25rem; font-size: 0.95rem; }}
.widget-paid-divider {{ border-top: 1px solid var(--border); margin: 0.65rem 0 0.45rem; }}
.widget-paid-details-title {{
  font-size: 0.7rem; font-weight: 700; color: var(--uagc-dark); margin: 0 0 0.25rem;
}}
.widget-paid-footnote {{ margin-bottom: 0.4rem; }}
.widget-comp-row {{ margin-bottom: 0.65rem; }}
.widget-comp-row:last-child {{ margin-bottom: 0; }}
.widget-comp-head {{ font-size: 0.7rem; font-weight: 600; color: var(--muted); margin-bottom: 0.25rem; display: flex; justify-content: space-between; }}
.widget-comp-total {{ font-weight: 500; color: var(--uagc-dark); }}

/* Navigation */
.back-to-top {{ position: fixed; bottom: 1.25rem; right: 1.25rem; background: var(--uagc-red); color: white; padding: 0.4rem 0.75rem; border-radius: 4px; text-decoration: none; font-size: 0.75rem; border: 1px solid var(--uagc-red); z-index: 100; }}

/* Methodology appendix */
.methodology-block {{ margin-top: 1.5rem; border-top: 2px solid var(--uagc-dark); padding-top: 1rem; }}
.methodology-intro {{ color: var(--muted); font-size: 0.82rem; margin-bottom: 1rem; max-width: 52rem; }}
.methodology-page {{ margin-bottom: 1.25rem; }}
.methodology-page h3 {{ color: var(--uagc-dark); font-size: 1.05rem; margin: 0 0 0.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.3rem; }}
.methodology-page h4 {{ font-size: 0.9rem; color: var(--uagc-dark); margin: 0.75rem 0 0.3rem; }}
.methodology-dl {{ font-size: 0.8rem; margin: 0 0 0.75rem; }}
.methodology-dl dt {{ font-weight: 600; color: var(--uagc-dark); margin-top: 0.4rem; }}
.methodology-dl dd {{ margin: 0.12rem 0 0 1rem; color: var(--text); }}
.methodology-list {{ font-size: 0.8rem; line-height: 1.45; color: var(--text); margin: 0.3rem 0 0.75rem 1.1rem; }}
.methodology-note {{ font-size: 0.78rem; color: var(--muted); margin: 0.4rem 0; }}
.methodology-table {{ width: 100%; border-collapse: collapse; font-size: 0.75rem; margin: 0.4rem 0 0.75rem; }}
.methodology-table th, .methodology-table td {{ border: 1px solid var(--border); padding: 0.28rem 0.4rem; text-align: left; vertical-align: top; }}
.methodology-table th {{ background: var(--uagc-dark); color: white; font-weight: 600; }}
.methodology-map-table {{ font-size: 0.7rem; }}
.methodology-map-table tbody tr:nth-child(even) {{ background: var(--surface-alt); }}

@media print {{
    .container {{ max-width: 100%; padding: 0.5rem; }}
    .detail-section {{ page-break-before: always; }}
    .methodology-page {{ page-break-before: always; }}
    .back-to-top {{ display: none; }}
    .tabs {{ display: none; }}
    .tab-content {{ display: block !important; }}
}}
@media (max-width: 768px) {{
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .lp-capture-grid {{ grid-template-columns: 1fr; }}
    .monthly-trend-body {{ grid-template-columns: 1fr; }}
    .profile-grid {{ grid-template-columns: 1fr; }}
    .detail-widgets {{ grid-template-columns: 1fr; }}
    .flow-kpi-grid {{ grid-template-columns: 1fr; }}
    .flow-balance {{ flex-direction: column; gap: 0.25rem; }}
    .flow-balance-arrow {{ transform: rotate(90deg); }}
}}
</style>
</head>
<body>
<div class="container">
    <h1>{REPORT_TITLE}</h1>
    <p class="subtitle">Lead funnel | {primary_label} vs YoY {prior_label} | {date.today().strftime('%B %d, %Y')}</p>
    <p class="sample-note">Summary matrix and <strong>full detail</strong> for every enrolling program ({len(undergrad_enrolling)} undergraduate, {len(graduate)} graduate). <strong>Level totals</strong>: {level_links_html}. Jump to <a href="#undergraduate-program-details">undergraduate details</a> or <a href="#graduate-program-details">graduate details</a>. <a href="#methodology">Methodology appendix</a> — formulas, mappings, and data sources. YoY mix &amp; program change analysis: <a href="program-insights.html">Program Insights</a> (standalone).</p>

    <a href="#top" class="back-to-top">&#8593; Top</a>

    <!-- TAB NAVIGATION -->
    <div id="top"></div>
    <div class="card">
        <h2>Summary Matrix</h2>
        <div class="tabs">
            <div class="tab active" onclick="switchTab('totals')">Totals</div>
            <div class="tab" onclick="switchTab('undergrad')">Undergraduate ({len(undergrad_enrolling)})</div>
            <div class="tab" onclick="switchTab('grad')">Graduate ({len(graduate)})</div>
            <div class="tab" onclick="switchTab('organization')">Organization</div>
        </div>
        <div class="tab-panel">
"""

def _matrix_row_metrics(pid: str, p: dict) -> dict:
    mig = p.get("_synthetic_migration")
    if mig is None and pid not in (
        "UNDECIDED_ROLLUP",
        UNDERGRAD_TOTAL_ID,
        GRADUATE_TOTAL_ID,
        OVERALL_TOTAL_ID,
    ):
        mig = migration.get(pid)
    pct_core = pct_core_from_widgets(detail_widgets, pid, p)
    mil, b2b = matrix_military_b2b_pct(demographics, detail_widgets, pid, p)
    core_enrolls = matrix_lob_enroll_count(
        detail_widgets,
        demographics,
        pid,
        CORE_LOB_LABELS,
        p,
        rollup_count_key="_rollup_core_enrolls",
    )
    military_enrolls = matrix_lob_enroll_count(
        detail_widgets,
        demographics,
        pid,
        MILITARY_LOB_LABELS,
        p,
        rollup_count_key="_rollup_military_enrolls",
    )
    b2b_enrolls = matrix_lob_enroll_count(
        detail_widgets,
        demographics,
        pid,
        B2B_LOB_LABELS,
        p,
        rollup_count_key="_rollup_b2b_enrolls",
    )
    return {
        'program_id': pid,
        'core_enrolls': core_enrolls,
        'core': pct_core,
        'military_enrolls': military_enrolls,
        'military': mil,
        'b2b_enrolls': b2b_enrolls,
        'b2b': b2b,
        'nav': p.get('pct_navigational'),
        'mig': mig,
    }


def _matrix_row(
    i: int | str,
    p: dict,
    metrics: dict,
    top_core: set[str],
    top_military: set[str],
    top_b2b: set[str],
    row_class: str = '',
    anchor_override: str | None = None,
    link_url: str | None = None,
    show_detail: bool | None = None,
    show_web_link: bool = True,
) -> str:
    pid = p['program_id']
    anchor = anchor_override or make_anchor(p['program_name'])
    url = link_url or PROGRAM_URLS.get(pid, '#')
    dec_rate = (p['decisions'] / p['leads'] * 100) if p['leads'] else 0
    enrl_rate = (p['new_enrollments'] / p['leads'] * 100) if p['leads'] else 0
    prior_chg = pct_change(p['decisions'], p['py_decisions'])
    if p.get("matrix_flag_new"):
        chg_html = change_icon_prior(None)
    else:
        chg_html = change_icon_prior(prior_chg)
    mig = metrics['mig']
    net_str, _ = fmt_net_cell(mig)
    net_enrl = net_enrollment_pct(mig, enrollment_view)
    net_enrl_str = f'{net_enrl:+.0f}%' if net_enrl is not None else '—'
    net_enrl_class = ''
    ev = enrollment_view(mig)
    net_val = ev.get('net_migration', 0) if ev else 0
    if net_val > 0:
        net_enrl_class = ' class="net-positive"'
    elif net_val < 0:
        net_enrl_class = ' class="net-negative"'
    net_td_classes = ['matrix-col-sep']
    if net_val > 0:
        net_td_classes.append('net-positive')
    elif net_val < 0:
        net_td_classes.append('net-negative')
    net_td_class = f' class="{" ".join(net_td_classes)}"'
    med_age, pct_fem = matrix_age_female(demographics, pid, p)
    if row_class:
        cls = f' class="{row_class}"'
    else:
        cls = ' class="matrix-row-data"'
    if show_detail is None:
        show_detail = pid in ALL_DETAIL_PROGRAM_IDS
    detail_link = (
        f'<a href="#{anchor}">Detail</a>'
        if show_detail
        else '<span class="link-muted">—</span>'
    )
    web_link = (
        f'<a href="{url}" target="_blank">Web</a>'
        if show_web_link and url and url != "#"
        else ""
    )
    links_cell = detail_link if not web_link else f"{detail_link}{web_link}"

    def matrix_cell_cls(base: str, top_set: set[str]) -> str:
        parts = [base] if base else []
        if pid in top_set:
            parts.append("matrix-top5")
        return f' class="{" ".join(parts)}"' if parts else ""

    core_enrl_cls = matrix_cell_cls("matrix-col-sep", top_core)
    core_pct_cls = matrix_cell_cls("", top_core)
    mil_cls = matrix_cell_cls("", top_military)
    b2b_cls = matrix_cell_cls("", top_b2b)

    group = p.get("account_group") or "—"
    prog_name = html_escape(p["program_name"])
    return (
        f'<tr{cls}><td>{i}</td>'
        f'<td class="matrix-program" title="{prog_name}">{prog_name}</td>'
        f'<td>{group}</td>'
        f'<td class="link-cell">{links_cell}</td>'
        f'<td>{p["leads"]:,}</td><td>{p["decisions"]:,}</td>'
        f'<td>{p["new_enrollments"]:,}</td>'
        f'<td>{fmt_matrix_pct(dec_rate)}</td><td>{fmt_matrix_pct(enrl_rate, decimals=1)}</td>'
        f'<td>{chg_html}</td>'
        f'<td{core_enrl_cls}>{fmt_matrix_count(metrics["core_enrolls"])}</td>'
        f'<td{core_pct_cls}>{fmt_matrix_pct(metrics["core"])}</td>'
        f'<td{mil_cls}>{fmt_matrix_pct(metrics["military"])}</td>'
        f'<td{b2b_cls}>{fmt_matrix_pct(metrics["b2b"])}</td>'
        f'<td>{fmt_matrix_pct(metrics["nav"])}</td>'
        f'<td{net_td_class}>{net_str}</td><td{net_enrl_class}>{net_enrl_str}</td>'
        f'<td>{med_age}</td><td>{pct_fem}</td></tr>\n'
    )


MATRIX_COLGROUP = (
    "<colgroup>"
    '<col style="width:3%">'
    '<col style="width:12%">'
    '<col style="width:5%">'
    '<col style="width:4%">'
    '<col style="width:5.5%">'
    '<col style="width:5.5%">'
    '<col style="width:4.5%">'
    '<col style="width:4%">'
    '<col style="width:4.5%">'
    '<col style="width:6%">'
    '<col style="width:4.5%">'
    '<col style="width:4%">'
    '<col style="width:4%">'
    '<col style="width:4%">'
    '<col style="width:5.5%">'
    '<col style="width:4%">'
    '<col style="width:4.5%">'
    '<col style="width:4%">'
    '<col style="width:4%">'
    "</colgroup>\n"
)


def _matrix_column_header_row(matric_label: str = "") -> str:
    matric_tip = matric_label or "current YoY window"
    return (
        '<tr class="matrix-cols-row">'
        "<th>#</th><th>Program</th><th>Group</th><th>Links</th>"
        "<th>Leads</th><th title=\"Application decisions\">Decisions</th>"
        "<th>Enrl</th><th title=\"Decisions ÷ leads\">Dec%</th>"
        "<th title=\"Enrollments ÷ leads\">Enrl%</th>"
        "<th title=\"Decisions vs prior YoY window\">Decision<br>YoY</th>"
        f'<th class="matrix-col-sep" title="Gross Core LOB enrollments (SRM matric {matric_tip})">'
        "# Core</th><th>% Core</th><th>% Mil</th><th>% B2B</th>"
        '<th title="Navigational share of final enrollments">% Navig</th>'
        '<th class="matrix-col-sep">Net</th><th>Net Enrl%</th><th>Med Age</th><th>% Female</th>'
        "</tr>\n"
    )


def _matrix_table_open(funnel_band: str, matric_label: str = "") -> str:
    return (
        '<div class="matrix-wrap">\n<table class="matrix-table">\n'
        f"{MATRIX_COLGROUP}<thead>\n"
        '<tr class="matrix-band-row">'
        '<th colspan="4" class="matrix-band matrix-band--id">Program</th>'
        f'<th colspan="6" class="matrix-band matrix-band--funnel">{funnel_band}</th>'
        '<th colspan="5" class="matrix-band matrix-band--lob matrix-col-sep">Enrollment mix</th>'
        '<th colspan="4" class="matrix-band matrix-band--profile matrix-col-sep">Migration &amp; profile</th>'
        "</tr>\n"
        + _matrix_column_header_row(matric_label)
    )


def render_matrix_table(
    progs: list[dict],
    tab_id: str,
    active: bool = False,
    level_rollup: dict | None = None,
    undecided_rollup: dict | None = None,
    period_label: str = "",
    rollup_rows: list[dict] | None = None,
    matric_label: str = "",
):
    active_cls = ' active' if active else ''
    if rollup_rows:
        all_progs = list(rollup_rows)
        row_metrics = [_matrix_row_metrics(p['program_id'], p) for p in all_progs]
        top_core = matrix_top_n_program_ids(row_metrics, 'core_enrolls')
        top_military = matrix_top_n_program_ids(row_metrics, 'military_enrolls')
        top_b2b = matrix_top_n_program_ids(row_metrics, 'b2b_enrolls')
        metrics_by_pid = {m['program_id']: m for m in row_metrics}
        funnel_band = period_label or "Funnel metrics"
        h = f'<div id="tab-{tab_id}" class="tab-content{active_cls}">\n'
        h += (
            '<p class="matrix-legend">'
            '<span><strong>Level rollups</strong> — undergraduate (includes undecided inquiry placeholders), graduate, and combined overall.</span> '
            '<span class="matrix-legend-top5">Top 5 gross LOB enrollments</span> · '
            '<span>Decision YoY: ▲/▼ beyond ±5%</span>'
            "</p>\n"
        )
        h += _matrix_table_open(funnel_band, matric_label) + "<tbody>\n"
        for i, p in enumerate(rollup_rows, 1):
            pid = p['program_id']
            h += _matrix_row(
                i,
                p,
                metrics_by_pid[pid],
                top_core,
                top_military,
                top_b2b,
                row_class='matrix-row-total',
                show_detail=pid in LEVEL_DETAIL_PROGRAM_IDS,
                link_url=LEVEL_DETAIL_URLS.get(pid),
                show_web_link=pid in LEVEL_DETAIL_URLS,
            )
        h += '</tbody></table>\n</div>\n</div>\n'
        return h

    all_progs = list(progs)
    if level_rollup:
        all_progs.insert(0, level_rollup)
    if undecided_rollup:
        all_progs.append(undecided_rollup)
    row_metrics = [_matrix_row_metrics(p['program_id'], p) for p in all_progs]
    top_core = matrix_top_n_program_ids(row_metrics, 'core_enrolls')
    top_military = matrix_top_n_program_ids(row_metrics, 'military_enrolls')
    top_b2b = matrix_top_n_program_ids(row_metrics, 'b2b_enrolls')
    metrics_by_pid = {m['program_id']: m for m in row_metrics}
    funnel_band = period_label or "Funnel metrics"

    h = f'<div id="tab-{tab_id}" class="tab-content{active_cls}">\n'
    h += (
        '<p class="matrix-legend">'
        '<span><strong>Read left to right:</strong> program identity, funnel, enrollment mix, migration &amp; profile.</span> '
        '<span class="matrix-legend-top5">Top 5 gross LOB enrollments</span> · '
        '<span>Decision YoY: ▲/▼ beyond ±5%</span> · '
        '<span>NEW = new launch or immaterial prior volume</span>'
        "</p>\n"
    )
    h += _matrix_table_open(funnel_band, matric_label) + "<tbody>\n"
    if level_rollup:
        pid = level_rollup['program_id']
        h += _matrix_row(
            '—',
            level_rollup,
            metrics_by_pid[pid],
            top_core,
            top_military,
            top_b2b,
            row_class='matrix-row-total',
            show_detail=pid in LEVEL_DETAIL_PROGRAM_IDS,
            link_url=LEVEL_DETAIL_URLS.get(pid),
            show_web_link=True,
        )
    for i, p in enumerate(progs, 1):
        pid = p['program_id']
        h += _matrix_row(
            i, p, metrics_by_pid[pid], top_core, top_military, top_b2b
        )
    if undecided_rollup:
        pid = undecided_rollup['program_id']
        h += _matrix_row(
            len(progs) + 1,
            undecided_rollup,
            metrics_by_pid[pid],
            top_core,
            top_military,
            top_b2b,
            row_class='matrix-row-undecided',
            anchor_override=make_anchor(UNDECIDED_DETAIL_LABEL),
            link_url=LEVEL_DETAIL_URLS.get(UNDECIDED_ROLLUP_ID),
            show_detail=True,
        )
    h += '</tbody></table>\n</div>\n</div>\n'
    return h


undergrad_all = undergrad_enrolling + undergrad_undecided
undergrad_total = aggregate_matrix_programs(
    undergrad_all,
    program_id=UNDERGRAD_TOTAL_ID,
    program_name=LEVEL_DETAIL_LABELS[UNDERGRAD_TOTAL_ID],
    account_group="—",
    degree_level="Undergraduate",
)
if undergrad_total:
    enrich_matrix_rollup_row(
        undergrad_total,
        [p["program_id"] for p in undergrad_all],
        detail_widgets,
        demographics,
        migration,
        enrollment_view,
    )

undecided_rollup = aggregate_undecided_programs(undergrad_undecided) if undergrad_undecided else None
if undecided_rollup:
    enrich_matrix_rollup_row(
        undecided_rollup,
        [p["program_id"] for p in undergrad_undecided],
        detail_widgets,
        demographics,
        migration,
        enrollment_view,
    )

graduate_total = aggregate_matrix_programs(
    graduate,
    program_id=GRADUATE_TOTAL_ID,
    program_name=LEVEL_DETAIL_LABELS[GRADUATE_TOTAL_ID],
    account_group="—",
    degree_level="Graduate",
)
if graduate_total:
    enrich_matrix_rollup_row(
        graduate_total,
        [p["program_id"] for p in graduate],
        detail_widgets,
        demographics,
        migration,
        enrollment_view,
    )

all_enrolling_programs = undergrad_all + graduate
overall_total = aggregate_matrix_programs(
    all_enrolling_programs,
    program_id=OVERALL_TOTAL_ID,
    program_name="Overall total",
    account_group="—",
    degree_level="All",
)
if overall_total:
    enrich_matrix_rollup_row(
        overall_total,
        [p["program_id"] for p in all_enrolling_programs],
        detail_widgets,
        demographics,
        migration,
        enrollment_view,
    )

undergrad_child_ids = [p["program_id"] for p in undergrad_all]
graduate_child_ids = [p["program_id"] for p in graduate]
if undergrad_total and undergrad_child_ids:
    detail_widgets[UNDERGRAD_TOTAL_ID] = rollup_detail_widgets(
        detail_widgets, undergrad_child_ids
    )
if graduate_total and graduate_child_ids:
    detail_widgets[GRADUATE_TOTAL_ID] = rollup_detail_widgets(
        detail_widgets, graduate_child_ids
    )

undecided_child_ids = [p["program_id"] for p in undergrad_undecided]
if undecided_rollup and undecided_child_ids:
    detail_widgets[UNDECIDED_ROLLUP_ID] = rollup_detail_widgets(
        detail_widgets, undecided_child_ids
    )

level_detail_specs: list[tuple[dict, list[str], list[dict]]] = []
if undergrad_total:
    level_detail_specs.append(
        (undergrad_total, undergrad_child_ids, undergrad_enrolling)
    )
if graduate_total:
    level_detail_specs.append((graduate_total, graduate_child_ids, graduate))

sankey_for_report = {
    pid: flow
    for pid, flow in sankey_flow.items()
    if pid in ENROLLING_DETAIL_PROGRAM_IDS
}
if undergrad_total and undergrad_child_ids:
    agg = aggregate_sankey_flow(sankey_flow, undergrad_child_ids)
    sankey_flow[UNDERGRAD_TOTAL_ID] = agg
    if agg.get("funnel", {}).get("inquiries", 0) > 0:
        sankey_for_report[UNDERGRAD_TOTAL_ID] = agg
if graduate_total and graduate_child_ids:
    agg = aggregate_sankey_flow(sankey_flow, graduate_child_ids)
    sankey_flow[GRADUATE_TOTAL_ID] = agg
    if agg.get("funnel", {}).get("inquiries", 0) > 0:
        sankey_for_report[GRADUATE_TOTAL_ID] = agg
if undecided_rollup and undecided_child_ids:
    agg = aggregate_sankey_flow(sankey_flow, undecided_child_ids)
    sankey_flow[UNDECIDED_ROLLUP_ID] = agg
    if agg.get("funnel", {}).get("inquiries", 0) > 0:
        sankey_for_report[UNDECIDED_ROLLUP_ID] = agg
    w = detail_widgets.get(UNDECIDED_ROLLUP_ID) or {}
    if not (w.get("marketing_segment") or {}).get("rollup_leads"):
        from_sankey = marketing_widgets_from_sankey_flow(agg)
        if from_sankey:
            detail_widgets[UNDECIDED_ROLLUP_ID] = from_sankey

totals_tab_rows: list[dict] = []
if overall_total:
    totals_tab_rows.append(overall_total)
totals_tab_rows.extend(
    sorted(
        [r for r in (undergrad_total, graduate_total) if r],
        key=matrix_sort_key,
    )
)
html += render_matrix_table(
    [],
    'totals',
    active=True,
    rollup_rows=totals_tab_rows,
    period_label=primary_label,
    matric_label=lob_matric_label,
)
html += render_matrix_table(
    undergrad_enrolling,
    'undergrad',
    level_rollup=undergrad_total or None,
    undecided_rollup=undecided_rollup,
    period_label=primary_label,
    matric_label=lob_matric_label,
)
html += render_matrix_table(
    graduate,
    'grad',
    level_rollup=graduate_total or None,
    period_label=primary_label,
    matric_label=lob_matric_label,
)

detail_programs_for_nav = undergrad_enrolling + graduate
org_level_links = [
    (LEVEL_DETAIL_LABELS[UNDERGRAD_TOTAL_ID], make_anchor(LEVEL_DETAIL_LABELS[UNDERGRAD_TOTAL_ID])),
    (LEVEL_DETAIL_LABELS[GRADUATE_TOTAL_ID], make_anchor(LEVEL_DETAIL_LABELS[GRADUATE_TOTAL_ID])),
]
html += render_organization_nav_tab(
    detail_programs_for_nav,
    alignment_by_pid,
    make_anchor=make_anchor,
    level_detail_links=org_level_links,
    undecided_label=UNDECIDED_DETAIL_LABEL if undecided_rollup else None,
    section_links=[
        ("All undergraduate details", "undergraduate-program-details"),
        ("All graduate details", "graduate-program-details"),
    ],
)

html += """        </div>
    </div>

"""


def _detail_header_ids_line(
    p: dict,
    *,
    level_detail: bool = False,
    undecided_detail: bool = False,
) -> str:
    pid = p.get("program_id", "")
    cvue = (p.get("program_code_cvue") or "").strip()
    if level_detail:
        return (
            f'<p class="meta meta-ids">Rollup program ID: <code>{html_escape(pid)}</code>'
            f" · CVue: not applicable (level aggregate)</p>\n"
        )
    if undecided_detail:
        return (
            f'<p class="meta meta-ids">Rollup program ID: <code>{html_escape(pid)}</code>'
            f" · CVue: not applicable (inquiry placeholders; see table below)</p>\n"
        )
    cvue_part = (
        f" · CVue: <code>{html_escape(cvue)}</code>"
        if cvue
        else " · CVue: not mapped"
    )
    return (
        f'<p class="meta meta-ids">Program ID: <code>{html_escape(pid)}</code>'
        f"{cvue_part}</p>\n"
    )


def _undecided_components_table(child_programs: list[dict]) -> str:
    if not child_programs:
        return ""
    rows = sorted(child_programs, key=lambda x: x.get("program_name", ""))
    h = (
        '<table class="undecided-components"><thead><tr>'
        "<th>Placeholder program</th><th>Program ID</th><th>CVue code</th>"
        "</tr></thead><tbody>\n"
    )
    for cp in rows:
        cvue = (cp.get("program_code_cvue") or "").strip() or "—"
        h += (
            "<tr>"
            f"<td>{html_escape(cp.get('program_name', ''))}</td>"
            f'<td class="mono">{html_escape(cp.get("program_id", ""))}</td>'
            f"<td>{html_escape(cvue)}</td>"
            "</tr>\n"
        )
    h += "</tbody></table>\n"
    return h


def render_program_detail(
    p: dict,
    period_primary: str,
    period_prior: str,
    peers: list[dict],
    monthly_label: str,
    *,
    level_detail: bool = False,
    undecided_detail: bool = False,
    child_program_ids: list[str] | None = None,
) -> str:
    pid = p['program_id']
    url = LEVEL_DETAIL_URLS.get(pid) or PROGRAM_URLS.get(pid, '#')
    if (level_detail or undecided_detail) and child_program_ids:
        months_data = fill_monthly_series(
            aggregate_monthly_series(monthly, child_program_ids, MONTHLY_DETAIL_MONTHS)
        )
        flow_data = sankey_flow.get(pid) or aggregate_sankey_flow(
            sankey_flow, child_program_ids
        )
    else:
        months_data = fill_monthly_series(monthly.get(pid, []))
        flow_data = sankey_flow.get(pid, {})

    lead_chg = pct_change(p['leads'], p['py_leads'])
    app_chg = pct_change(p['apps_started'], p['py_apps_started'])
    dec_chg = pct_change(p['decisions'], p['py_decisions'])
    enrl_chg = pct_change(p['new_enrollments'], p['py_new_enrollments'])

    if undecided_detail:
        display_name = UNDECIDED_DETAIL_LABEL
    elif level_detail:
        display_name = LEVEL_DETAIL_LABELS.get(pid, p["program_name"])
    else:
        display_name = p["program_name"]
    anchor = make_anchor(display_name)
    section_cls = "detail-section"
    if level_detail:
        section_cls += " detail-section--level-total"
    if undecided_detail:
        section_cls += " detail-section--undecided"
    block = f'    <div class="{section_cls}" id="{anchor}">\n'
    block += '        <div class="detail-header">\n'
    block += f'            <h3>{html_escape(display_name)}</h3>\n'
    if undecided_detail:
        n_child = len(child_program_ids) if child_program_ids else 0
        scope = (
            f"Undergraduate inquiry placeholders · {n_child} Salesforce programs rolled up"
        )
        block += f'            <p class="meta">{scope} | '
        block += (
            f'<a href="{url}" target="_blank">View online degrees hub &rarr;</a></p>\n'
        )
    elif level_detail:
        block += (
            '            <p class="meta">All programs at this degree level (matrix total row) | '
            f'<a href="{url}" target="_blank">View Landing Page &rarr;</a></p>\n'
        )
    else:
        block += (
            f'            <p class="meta">{html_escape(p["degree_level"])} | '
            f'{html_escape(p.get("degree_type", ""))} | '
            f'<a href="{url}" target="_blank">View Landing Page &rarr;</a></p>\n'
        )
    block += _detail_header_ids_line(
        p, level_detail=level_detail, undecided_detail=undecided_detail
    )
    block += f'            <p class="meta">Metrics: {period_primary} vs YoY {period_prior}</p>\n'
    block += '        </div>\n\n'

    if not level_detail and not undecided_detail:
        block += render_academic_alignment_section(alignment_by_pid.get(pid))

    block += '        <div class="kpi-grid">\n'
    for label, val, chg in [
        (f'Leads ({period_primary})', p['leads'], lead_chg),
        ('Apps Started', p['apps_started'], app_chg),
        ('Decisions', p['decisions'], dec_chg),
        ('Final Enrollments', p['new_enrollments'], enrl_chg),
    ]:
        block += (
            f'            <div class="kpi"><div class="value">{val:,}</div>'
            f'<div class="label">{label}</div>{change_icon(chg)}</div>\n'
        )
    block += '        </div>\n\n'

    sankey_html = render_sankey_host(
        pid,
        flow_data,
        level_aggregate=level_detail,
        undecided_aggregate=undecided_detail,
    )
    if sankey_html:
        block += sankey_html

    if level_detail:
        n_programs = len(child_program_ids) if child_program_ids else 0
        enr = p.get("new_enrollments", 0)
        leads = p.get("leads", 0)
        enr_rate = (enr / leads * 100) if leads else 0
        undecided_note = (
            " (including undecided inquiry placeholders)"
            if p.get("degree_level") == "Undergraduate"
            else ""
        )
        block += (
            '        <div class="card summary-card">\n'
            f'<p><strong>{html_escape(display_name)}</strong> rolls up <strong>{n_programs:,}</strong> '
            f'programs{undecided_note}. '
            f'In {period_primary} the level generated <strong>{leads:,}</strong> inquiries and '
            f'<strong>{enr:,}</strong> final enrollments ({enr_rate:.2f}% inquiry-to-enrollment). '
            f'Metrics and charts below sum or weight across those programs.</p>\n'
            '        </div>\n\n'
        )
    elif undecided_detail:
        n_child = len(child_program_ids) if child_program_ids else 0
        enr = p.get("new_enrollments", 0)
        leads = p.get("leads", 0)
        enr_rate = (enr / leads * 100) if leads else 0
        child_programs = [
            program_by_id[cid]
            for cid in (child_program_ids or [])
            if cid in program_by_id
        ]
        block += (
            '        <div class="card summary-card">\n'
            f'<p><strong>{html_escape(display_name)}</strong> combines <strong>{n_child}</strong> '
            "undergraduate Salesforce programs used when a lead has not selected a "
            "degree-specific program. "
            f"In {period_primary} the group generated <strong>{leads:,}</strong> inquiries and "
            f"<strong>{enr:,}</strong> final enrollments ({enr_rate:.2f}% inquiry-to-enrollment). "
            "Sankey and marketing-segment views below aggregate inquiry volume across these "
            "placeholders; per-program migration and enrolled-student profile are omitted.</p>\n"
            + _undecided_components_table(child_programs)
            + "        </div>\n\n"
        )
    else:
        level_ref = (
            undergrad_total
            if p.get("degree_level") == "Undergraduate"
            else graduate_total
        )
        block += build_program_summary(
            p,
            peers,
            period_primary,
            period_prior,
            detail_widgets,
            demographics,
            demo_baselines,
            migration,
            enrollment_view,
            level_ref=level_ref,
        )

    if level_detail and child_program_ids:
        demo_prof = rollup_demographics_profile(
            demographics,
            child_program_ids,
            label=p["program_name"],
        )
    elif undecided_detail:
        demo_prof = None
    else:
        demo_prof = demographics.get(pid)
    region_html = ""
    if demo_prof and not undecided_detail:
        region_html = render_state_region_section(
            demo_prof, demo_baselines, p['degree_level'], embedded=True
        )
    widgets_html = render_detail_widgets(pid, region_html=region_html)
    if widgets_html:
        block += widgets_html

    if level_detail or undecided_detail:
        mig = p.get("_synthetic_migration")
        flow_html = render_level_migration_block(mig)
    else:
        mig = migration.get(pid)
        flow_html = render_migration_sections(mig, p['program_name'])
    if flow_html:
        block += flow_html

    demo_html = render_demographics_section(
        demo_prof,
        p['program_name'],
        p['degree_level'],
        demo_baselines,
        demo_matric_label,
    )
    if demo_html:
        block += demo_html

    if months_data:
        block += render_monthly_volume_section(months_data, monthly_label)

    block += render_landing_screenshots(pid, url)

    block += '    </div>\n\n'
    return block


# ========== LEVEL TOTAL DETAIL PAGES ==========
if level_detail_specs:
    html += (
        '    <div class="card" style="margin-top:2.5rem;border-top:3px solid var(--uagc-dark);">\n'
        '        <h2>Undergraduate &amp; graduate totals</h2>\n'
        '        <p class="sample-note" style="margin-bottom:1.25rem;">'
        'Aggregated metrics for all programs at each degree level (including Sankey inflow '
        'and funnel); landing pages are the degree-level hubs on uagc.edu. '
        'Enrollment migration and inquiry-vs-applied flow are not shown at this level '
        '(see per-program detail pages).</p>\n'
    )
    for p, child_ids, peers in level_detail_specs:
        html += render_program_detail(
            p,
            primary_label,
            prior_label,
            peers,
            monthly_detail_label,
            level_detail=True,
            child_program_ids=child_ids,
        )
    html += "    </div>\n"

# ========== UNDECIDED GROUP DETAIL ==========
if undecided_rollup and undecided_child_ids:
    html += (
        '    <div class="card" style="margin-top:2.5rem;border-top:3px solid var(--muted);">\n'
        '        <h2>Undecided inquiry placeholders</h2>\n'
        '        <p class="sample-note" style="margin-bottom:1.25rem;">'
        'Aggregated lead funnel and marketing inflow for undergraduate inquiry-placeholder '
        'programs (rolled up in the undergraduate matrix tab). Migration and enrolled-student '
        'profile are not shown at this grouping level.</p>\n'
    )
    html += render_program_detail(
        undecided_rollup,
        primary_label,
        prior_label,
        undergrad_undecided,
        monthly_detail_label,
        undecided_detail=True,
        child_program_ids=undecided_child_ids,
    )
    html += "    </div>\n"

# ========== ALL PROGRAM DETAIL PAGES ==========
html += (
    '    <div class="card" style="margin-top:2.5rem;border-top:3px solid var(--uagc-red);">\n'
    '        <h2 id="undergraduate-program-details">Undergraduate program details</h2>\n'
    '        <p class="sample-note" style="margin-bottom:1.25rem;">'
    f'Sorted by final enrollments ({primary_label}). Sankey, migration, enrolled-student profile, '
    'monthly volume, and landing-page captures per program.</p>\n'
)
for p in undergrad_enrolling:
    html += render_program_detail(
        p, primary_label, prior_label, undergrad_enrolling, monthly_detail_label
    )
html += (
    '    </div>\n'
    '    <div class="card" style="margin-top:2.5rem;border-top:3px solid var(--uagc-dark);">\n'
    '        <h2 id="graduate-program-details">Graduate program details</h2>\n'
    '        <p class="sample-note" style="margin-bottom:1.25rem;">'
    f'Sorted by final enrollments ({primary_label}).</p>\n'
)
for p in graduate:
    html += render_program_detail(
        p, primary_label, prior_label, graduate, monthly_detail_label
    )
html += '    </div>\n'

html += render_methodology_appendix()

# JavaScript for tabs + Sankey
html += """</div>

"""
html += sankey_script_block(sankey_for_report)
html += """<script>
function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    event.target.classList.add('active');
}
function initLandingCaptures() {
    document.querySelectorAll('.lp-device').forEach(function(device) {
        var img = device.querySelector('.lp-shot');
        var viewport = device.querySelector('.lp-viewport');
        if (!img || !viewport) return;
        device.querySelectorAll('.lp-nav-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var frame = btn.getAttribute('data-frame');
                var src = img.getAttribute('data-' + frame);
                if (!src) return;
                device.querySelectorAll('.lp-nav-btn').forEach(function(b) {
                    var on = b === btn;
                    b.classList.toggle('is-active', on);
                    b.setAttribute('aria-selected', on ? 'true' : 'false');
                });
                img.src = src;
                img.alt = btn.textContent.trim();
                viewport.classList.remove('lp-viewport--slice', 'lp-viewport--full');
                viewport.classList.add(frame === 'full' ? 'lp-viewport--full' : 'lp-viewport--slice');
                viewport.scrollTop = 0;
            });
        });
    });
}
document.addEventListener('DOMContentLoaded', initLandingCaptures);
</script>
</body>
</html>"""

DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
output_path = DEPLOY_DIR / 'index.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

copied = sync_screenshots_to_deploy(None)
size_mb = output_path.stat().st_size / (1024 * 1024)
print(f"\nReport generated: {output_path}")
if copied:
    print(f"Screenshots copied to deploy/screenshots: {copied} files")
else:
    print("No screenshots in screenshots/ — run capture_all_screenshots.py")
print(f"File size: {size_mb:.1f} MB")
print(
    f"Matrix: {len(undergrad_enrolling)} undergrad + {len(graduate)} graduate "
    f"({len(undergrad_undecided)} undecided in rollup)"
)
undecided_detail_n = 1 if undecided_rollup and undecided_child_ids else 0
print(
    f"Detail pages: {len(level_detail_specs)} level totals + "
    f"{undecided_detail_n} undecided group + "
    f"{len(ENROLLING_DETAIL_PROGRAM_IDS)} programs"
)
