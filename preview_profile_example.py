"""Build a single-program HTML preview for profile + summary changes."""
from __future__ import annotations

import json
from pathlib import Path

from generate_full_report import (
    PROGRAM_URLS,
    demo_baselines,
    demographics,
    demo_matric_label,
    detail_widgets,
    enrollment_view,
    make_anchor,
    migration,
    monthly,
    monthly_detail_label,
    primary_label,
    prior_label,
    render_demographics_section,
    render_program_detail,
)
from report_periods import SAMPLE_DETAIL_PROGRAM_IDS

ROOT = Path(__file__).resolve().parent
EXAMPLE_PID = "001Do00000ScUzFIAV"  # BA in Psychology

with open(ROOT / "program_data_full.json", encoding="utf-8") as f:
    programs = json.load(f)["programs"]

program = next(p for p in programs if p["program_id"] == EXAMPLE_PID)
peers = [p for p in programs if p["degree_level"] == program["degree_level"]]

detail_html = render_program_detail(
    program, primary_label, prior_label, peers, monthly_detail_label
)

css = (ROOT / "deploy" / "index.html").read_text(encoding="utf-8")
style_start = css.find("<style>")
style_end = css.find("</style>") + len("</style>")
head = css[style_start:style_end]

out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Profile preview — BA in Psychology</title>
{head}
</head>
<body>
<div class="container">
<p class="subtitle">Preview: enrolled student profile + program summary changes (not deployed to Pages yet).</p>
{detail_html}
</div>
</body>
</html>
"""

out_path = ROOT / "deploy" / "profile-preview-psychology.html"
out_path.write_text(out, encoding="utf-8")
print(f"Wrote {out_path}")
