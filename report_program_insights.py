"""Build standalone program changes & mix YoY insights HTML."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

from report_periods import PRIMARY_LABEL, PRIOR_LABEL

ROOT = Path(__file__).resolve().parent
MIX_PATH = ROOT / "portfolio_mix_yoy.json"
DATA_PATH = ROOT / "program_data_full.json"
BRIDGE_PATH = ROOT / "data" / "program_srm_bridge.json"

CHANGE_THRESHOLD_PCT = 5.0
MIN_ENROLLS_FOR_MOVER = 15


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _pct_map(rows: list[dict]) -> dict[str, float]:
    return {r["label"]: r["pct"] for r in rows}


def _delta_pp(cur: float | None, prior: float | None) -> float | None:
    if cur is None or prior is None:
        return None
    return cur - prior


def _fmt_pct(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "—"


def _fmt_delta_pp(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1f}pp"


def _pct_change(cur: int, prior: int) -> float | None:
    if prior == 0:
        return None if cur == 0 else float("inf")
    return (cur - prior) / prior * 100


def _chg_label(pct: float | None) -> str:
    if pct is None:
        return "—"
    if pct == float("inf"):
        return "NEW"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.0f}%"


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _mix_narrative(mix: dict) -> str:
    overall = mix["slices"]["overall"]
    pri_e = _pct_map(overall["primary"]["level_mix"]["enrollments"])
    pyr_e = _pct_map(overall["prior"]["level_mix"]["enrollments"])
    pri_lob = _pct_map(overall["primary"]["lob_enrollments"])
    pyr_lob = _pct_map(overall["prior"]["lob_enrollments"])

    bullets: list[str] = []
    ug_d = _delta_pp(pri_e.get("Undergraduate"), pyr_e.get("Undergraduate"))
    gr_d = _delta_pp(pri_e.get("Graduate"), pyr_e.get("Graduate"))
    if ug_d is not None and gr_d is not None:
        if abs(ug_d) >= 2 or abs(gr_d) >= 2:
            bullets.append(
                f"Enrollment mix shifted toward "
                f"{'undergraduate' if ug_d > 0 else 'graduate'} programs "
                f"(UG {_fmt_delta_pp(ug_d)}, Grad {_fmt_delta_pp(gr_d)})."
            )

    lob_shifts: list[tuple[str, float]] = []
    for lob in ("Core", "Full Tuition Grant", "Tuition Benefit", "Military"):
        d = _delta_pp(pri_lob.get(lob), pyr_lob.get(lob))
        if d is not None and abs(d) >= 2:
            lob_shifts.append((lob, d))
    lob_shifts.sort(key=lambda x: abs(x[1]), reverse=True)
    for lob, d in lob_shifts[:3]:
        direction = "up" if d > 0 else "down"
        bullets.append(f"{lob} enrollment share {direction} {_fmt_delta_pp(d)} vs prior year.")

    if not bullets:
        bullets.append(
            "Portfolio enrollment mix by degree level and LOB was broadly stable year-over-year."
        )
    return "<ul class=\"insight-list\">" + "".join(f"<li>{_esc(b)}</li>" for b in bullets) + "</ul>"


def _portfolio_totals(programs: list[dict]) -> dict[str, dict[str, int]]:
    keys = ("leads", "decisions", "new_enrollments")
    cur = {k: sum(p[k] for p in programs) for k in keys}
    prior = {
        "leads": sum(p["py_leads"] for p in programs),
        "decisions": sum(p["py_decisions"] for p in programs),
        "new_enrollments": sum(p["py_new_enrollments"] for p in programs),
    }
    return {"current": cur, "prior": prior}


def _program_movers(programs: list[dict]) -> list[dict]:
    rows = []
    for p in programs:
        if p.get("matrix_flag_new"):
            continue
        enr = p["new_enrollments"]
        py_enr = p["py_new_enrollments"]
        if enr < MIN_ENROLLS_FOR_MOVER and py_enr < MIN_ENROLLS_FOR_MOVER:
            continue
        rows.append(
            {
                "program_id": p["program_id"],
                "program_name": p["program_name"],
                "degree_level": p.get("degree_level", ""),
                "leads": p["leads"],
                "py_leads": p["py_leads"],
                "leads_chg": _pct_change(p["leads"], p["py_leads"]),
                "decisions": p["decisions"],
                "py_decisions": p["py_decisions"],
                "decisions_chg": _pct_change(p["decisions"], p["py_decisions"]),
                "enrollments": enr,
                "py_enrollments": py_enr,
                "enrollments_chg": _pct_change(enr, py_enr),
            }
        )
    return rows


def _movers_table(
    rows: list[dict],
    title: str,
    *,
    limit: int = 12,
    reverse: bool = True,
) -> str:
    sorted_rows = sorted(
        rows,
        key=lambda r: r["enrollments_chg"] if r["enrollments_chg"] is not None else -999,
        reverse=reverse,
    )
    body = ""
    for r in sorted_rows[:limit]:
        body += (
            "<tr>"
            f"<td>{_esc(r['program_name'])}</td>"
            f"<td>{_esc(r['degree_level'])}</td>"
            f"<td>{r['enrollments']:,}</td>"
            f"<td>{r['py_enrollments']:,}</td>"
            f"<td>{_esc(_chg_label(r['enrollments_chg']))}</td>"
            f"<td>{r['decisions']:,}</td>"
            f"<td>{_esc(_chg_label(r['decisions_chg']))}</td>"
            "</tr>"
        )
    if not body:
        return f"<h3>{_esc(title)}</h3><p class=\"muted\">No programs met volume threshold.</p>"
    return f"""
    <h3>{_esc(title)}</h3>
    <table class="data-table">
      <thead><tr>
        <th>Program</th><th>Level</th>
        <th>Enrl (current)</th><th>Enrl (prior)</th><th>Enrl YoY</th>
        <th>Decisions</th><th>Dec YoY</th>
      </tr></thead>
      <tbody>{body}</tbody>
    </table>
    """


def _mix_section(mix: dict) -> str:
    pri_w = _esc(mix["primary_window"]["label"])
    pyr_w = _esc(mix["prior_window"]["label"])
    narrative = _mix_narrative(mix)

    tables = ""
    for key, heading in (
        ("overall", "Overall portfolio"),
        ("undergraduate", "Undergraduate programs"),
        ("graduate", "Graduate programs"),
    ):
        sl = mix["slices"][key]
        tables += f"<section class=\"insight-block\"><h3>{_esc(heading)}</h3>"
        if key == "overall":
            pri_e = sl["primary"]["level_mix"]["enrollments"]
            pyr_e = sl["prior"]["level_mix"]["enrollments"]
            pri_d = sl["primary"]["level_mix"]["decisions"]
            pyr_d = sl["prior"]["level_mix"]["decisions"]
            rows = ""
            for level in ("Undergraduate", "Graduate"):
                pe = _pct_map(pri_e).get(level)
                py = _pct_map(pyr_e).get(level)
                pd = _pct_map(pri_d).get(level)
                pyd = _pct_map(pyr_d).get(level)
                rows += (
                    "<tr>"
                    f"<td>{_esc(level)}</td>"
                    f"<td>{_fmt_pct(pd)}</td><td>{_fmt_pct(pyd)}</td>"
                    f"<td>{_fmt_delta_pp(_delta_pp(pd, pyd))}</td>"
                    f"<td>{_fmt_pct(pe)}</td><td>{_fmt_pct(py)}</td>"
                    f"<td>{_fmt_delta_pp(_delta_pp(pe, py))}</td>"
                    "</tr>"
                )
            tables += f"""
            <table class="data-table">
              <thead><tr>
                <th>Level</th>
                <th colspan="3">Decisions mix</th>
                <th colspan="3">Enrollment mix (BQ)</th>
              </tr>
              <tr><th></th>
                <th>Current</th><th>Prior</th><th>Δ</th>
                <th>Current</th><th>Prior</th><th>Δ</th>
              </tr></thead>
              <tbody>{rows}</tbody>
            </table>
            """

        pri_lob = sl["primary"]["lob_enrollments"]
        pyr_lob = sl["prior"]["lob_enrollments"]
        lob_rows = ""
        for lob in ("Core", "Full Tuition Grant", "Tuition Benefit", "Military"):
            cp = _pct_map(pri_lob).get(lob)
            pp = _pct_map(pyr_lob).get(lob)
            if cp is None and pp is None:
                continue
            lob_rows += (
                "<tr>"
                f"<td>{_esc(lob)}</td>"
                f"<td>{_fmt_pct(cp)}</td><td>{_fmt_pct(pp)}</td>"
                f"<td>{_fmt_delta_pp(_delta_pp(cp, pp))}</td>"
                "</tr>"
            )
        tables += f"""
        <h4>Enrollment LOB mix (SRM matriculations)</h4>
        <table class="data-table">
          <thead><tr><th>LOB</th><th>Current</th><th>Prior YoY</th><th>Δ</th></tr></thead>
          <tbody>{lob_rows}</tbody>
        </table>
        </section>
        """

    return f"""
    <section id="mix-analysis" class="panel-section">
      <h2>Enrollment mix analysis</h2>
      <p class="lead">
        Portfolio composition for <strong>{pri_w}</strong> compared with
        <strong>{pyr_w}</strong>. LOB reflects SRM matriculations; degree-level
        splits use BigQuery funnel enrollments and decisions.
      </p>
      {narrative}
      {tables}
    </section>
    """


def _program_changes_section(programs: list[dict], totals: dict) -> str:
    cur = totals["current"]
    prior = totals["prior"]
    movers = _program_movers(programs)
    gainers = sorted(
        [m for m in movers if m["enrollments_chg"] is not None and m["enrollments_chg"] > CHANGE_THRESHOLD_PCT],
        key=lambda m: m["enrollments_chg"],
        reverse=True,
    )
    decliners = sorted(
        [m for m in movers if m["enrollments_chg"] is not None and m["enrollments_chg"] < -CHANGE_THRESHOLD_PCT],
        key=lambda m: m["enrollments_chg"],
    )

    summary_rows = ""
    for label, key in (
        ("Leads", "leads"),
        ("Decisions", "decisions"),
        ("Enrollments", "new_enrollments"),
    ):
        c, p = cur[key], prior[key]
        summary_rows += (
            "<tr>"
            f"<td>{label}</td><td>{c:,}</td><td>{p:,}</td>"
            f"<td>{_esc(_chg_label(_pct_change(c, p)))}</td>"
            "</tr>"
        )

    insight_bits = []
    if gainers:
        top = gainers[0]
        insight_bits.append(
            f"Largest enrollment gain: {top['program_name']} ({_chg_label(top['enrollments_chg'])} YoY)."
        )
    if decliners:
        top = decliners[0]
        insight_bits.append(
            f"Largest enrollment decline: {top['program_name']} ({_chg_label(top['enrollments_chg'])} YoY)."
        )
    if not insight_bits:
        insight_bits.append("No single program exceeded ±5% enrollment change at the minimum volume threshold.")

    insights_ul = "<ul class=\"insight-list\">" + "".join(
        f"<li>{_esc(b)}</li>" for b in insight_bits
    ) + "</ul>"

    return f"""
    <section id="program-changes" class="panel-section">
      <h2>Program change insights</h2>
      <p class="lead">
        Year-over-year volume at the program level. Programs need at least
        {MIN_ENROLLS_FOR_MOVER} enrollments in either window to appear in mover tables.
        Flagged changes use a ±{CHANGE_THRESHOLD_PCT:.0f}% enrollment threshold.
      </p>
      <h3>Portfolio funnel totals</h3>
      <table class="data-table compact">
        <thead><tr><th>Metric</th><th>{_esc(PRIMARY_LABEL)}</th><th>{_esc(PRIOR_LABEL)}</th><th>YoY</th></tr></thead>
        <tbody>{summary_rows}</tbody>
      </table>
      {insights_ul}
      {_movers_table(gainers, "Enrollment gainers (YoY > +5%)")}
      {_movers_table(decliners, "Enrollment decliners (YoY < −5%)", reverse=False)}
      <p class="muted note">
        Full per-program metrics remain in the
        <a href="index.html">Program Performance Report</a> matrix and detail pages.
        This document is the analysis layer only.
      </p>
    </section>
    """


def _technical_section() -> str:
    return f"""
    <section id="technical" class="panel-section">
      <h2>Technical details</h2>
      <dl class="tech-dl">
        <dt>Primary window</dt><dd>{_esc(PRIMARY_LABEL)}</dd>
        <dt>Prior YoY window</dt><dd>{_esc(PRIOR_LABEL)}</dd>
        <dt>Mix data</dt><dd><code>pull_portfolio_mix_yoy.py</code> → <code>portfolio_mix_yoy.json</code></dd>
        <dt>Program volumes</dt><dd><code>pull_full_data.py</code> → <code>program_data_full.json</code></dd>
        <dt>Regenerate</dt><dd><code>uv run python generate_program_insights.py</code></dd>
      </dl>
      <p class="muted">
        Degree-level mix: BigQuery <code>vw_lead_extract_details</code> with
        <code>is_new_enrollment_final</code> / <code>is_appin</code>.
        LOB mix: SQL Server <code>StudentRevenueMaster</code> matric dates aligned to the same windows.
      </p>
    </section>
    """


def _roadmap_section() -> str:
    return """
    <section id="roadmap" class="panel-section">
      <h2>Roadmap</h2>
      <ul class="insight-list">
        <li><strong>Done:</strong> Portfolio mix YoY (degree level + LOB) and program volume movers.</li>
        <li><strong>Next:</strong> Segment / channel mix YoY at portfolio and level rollups.</li>
        <li><strong>Next:</strong> Per-program LOB mix shift (standalone table, not on detail profiles).</li>
        <li><strong>Later:</strong> Tie insights to Christine product-strategy framework (keep / reformat / restrict / exit).</li>
      </ul>
    </section>
    """


def render_insights_html(
    mix: dict | None = None,
    program_data: dict | None = None,
    report_date: date | None = None,
) -> str:
    when = (report_date or date.today()).strftime("%B %d, %Y")
    mix = mix or _load_json(MIX_PATH)
    program_data = program_data or _load_json(DATA_PATH)
    programs = program_data.get("programs", []) if program_data else []
    totals = _portfolio_totals(programs) if programs else {"current": {}, "prior": {}}

    mix_html = (
        _mix_section(mix)
        if mix
        else '<section class="panel-section"><p>Run <code>pull_portfolio_mix_yoy.py</code> first.</p></section>'
    )
    changes_html = (
        _program_changes_section(programs, totals)
        if programs
        else '<section class="panel-section"><p>Run <code>pull_full_data.py</code> first.</p></section>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UAGC Program Changes &amp; Mix Insights</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --uagc-red: #AB0520;
  --uagc-dark: #0C234B;
  --highlight-blue: #0076A8;
  --text: #53565A;
  --muted: #98A4AE;
  --border: #D0D0CE;
  --surface: #f4f4f3;
  --card: #fff;
}}
* {{ box-sizing: border-box; }}
body {{
  font-family: Montserrat, system-ui, sans-serif;
  color: var(--text); background: var(--surface);
  margin: 0; line-height: 1.5;
}}
.container {{ max-width: 960px; margin: 0 auto; padding: 1.25rem 1rem 2rem; }}
header {{ border-bottom: 3px solid var(--uagc-red); padding-bottom: 0.75rem; margin-bottom: 1rem; }}
h1 {{ color: var(--uagc-dark); font-size: 1.35rem; margin: 0 0 0.25rem; }}
.subtitle {{ color: var(--muted); font-size: 0.85rem; margin: 0; }}
.tabs {{ display: flex; flex-wrap: wrap; gap: 0; margin: 1rem 0 0; }}
.tab {{
  padding: 0.5rem 1rem; cursor: pointer; border: 1px solid var(--border);
  border-bottom: none; background: var(--surface); color: var(--muted);
  font-weight: 600; font-size: 0.78rem; border-radius: 6px 6px 0 0;
}}
.tab.active {{ background: var(--card); color: var(--uagc-dark); }}
.tab-panel {{
  background: var(--card); border: 1px solid var(--border);
  border-radius: 0 6px 6px 6px; padding: 1rem 1.1rem;
}}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.panel-section {{ margin-bottom: 1.5rem; }}
.panel-section h2 {{ color: var(--uagc-dark); font-size: 1.05rem; margin: 0 0 0.5rem; }}
.panel-section h3 {{ font-size: 0.92rem; color: var(--uagc-dark); margin: 1rem 0 0.4rem; }}
.panel-section h4 {{ font-size: 0.82rem; margin: 0.75rem 0 0.35rem; }}
.lead {{ font-size: 0.88rem; max-width: 44rem; margin-bottom: 0.75rem; }}
.insight-list {{ font-size: 0.85rem; margin: 0.5rem 0 1rem 1.2rem; }}
.insight-list li {{ margin-bottom: 0.35rem; }}
.data-table {{
  width: 100%; border-collapse: collapse; font-size: 0.78rem; margin: 0.5rem 0 1rem;
}}
.data-table th, .data-table td {{
  border: 1px solid var(--border); padding: 0.35rem 0.5rem; text-align: right;
}}
.data-table th:first-child, .data-table td:first-child {{ text-align: left; }}
.data-table th {{ background: var(--uagc-dark); color: #fff; font-weight: 600; }}
.data-table tbody tr:nth-child(even) {{ background: var(--surface); }}
.muted {{ color: var(--muted); font-size: 0.8rem; }}
.note {{ margin-top: 1rem; }}
.tech-dl {{ font-size: 0.82rem; }}
.tech-dl dt {{ font-weight: 600; color: var(--uagc-dark); margin-top: 0.5rem; }}
.tech-dl dd {{ margin: 0.1rem 0 0 1rem; }}
a {{ color: var(--highlight-blue); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Program Changes &amp; Mix Insights</h1>
    <p class="subtitle">YoY analysis · {_esc(PRIMARY_LABEL)} vs {_esc(PRIOR_LABEL)} · {when}</p>
    <p class="subtitle">Companion to the <a href="index.html">Program Performance Report</a> — analysis only, not embedded in program profiles.</p>
  </header>

  <div class="tabs" role="tablist">
    <div class="tab active" data-tab="analysis" role="tab">Analysis</div>
    <div class="tab" data-tab="technical" role="tab">Technical</div>
    <div class="tab" data-tab="roadmap" role="tab">Roadmap</div>
  </div>
  <div class="tab-panel">
    <div id="tab-analysis" class="tab-content active">
      {mix_html}
      {changes_html}
    </div>
    <div id="tab-technical" class="tab-content">
      {_technical_section()}
    </div>
    <div id="tab-roadmap" class="tab-content">
      {_roadmap_section()}
    </div>
  </div>
</div>
<script>
(function() {{
  const tabs = document.querySelectorAll('.tab');
  const panels = document.querySelectorAll('.tab-content');
  function activate(id) {{
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === id));
    panels.forEach(p => p.classList.toggle('active', p.id === 'tab-' + id));
    history.replaceState(null, '', '#' + id);
  }}
  tabs.forEach(t => t.addEventListener('click', () => activate(t.dataset.tab)));
  const hash = location.hash.replace('#', '');
  if (hash && document.getElementById('tab-' + hash)) activate(hash);
}})();
</script>
</body>
</html>
"""
