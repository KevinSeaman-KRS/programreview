"""Generate standalone program changes & mix YoY insights HTML."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from report_program_insights import _load_json, render_insights_html

ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "deploy" / "program-insights.html"


def main() -> None:
    mix = _load_json(ROOT / "portfolio_mix_yoy.json")
    program_data = _load_json(ROOT / "program_data_full.json")
    html = render_insights_html(mix=mix, program_data=program_data, report_date=date.today())
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Insights report: {OUT_PATH} ({len(html) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
