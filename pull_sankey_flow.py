"""
Per-program Sankey data: marketing_segment_rollup inflow + funnel (primary window).
Output: program_sankey_flow.json
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from google.cloud import bigquery

from marketing_segment_hierarchy import SEGMENT1_ORDER, resolve_segment1
from report_periods import PRIMARY_END, PRIMARY_LABEL, PRIMARY_START

ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "program_sankey_flow.json"

SKIP_SEGMENT_RE = re.compile(r"^(unknown|other|\(unknown\)|\(null\))$", re.I)


def should_skip_segment(segment: str | None) -> bool:
    if segment is None:
        return True
    s = str(segment).strip()
    return not s or bool(SKIP_SEGMENT_RE.match(s))


def main() -> None:
    data = json.loads((ROOT / "program_data_full.json").read_text(encoding="utf-8"))
    funnel = data.get("funnel", {})
    id_list = [p["program_id"] for p in data["programs"]]
    id_sql = ", ".join(f"'{i}'" for i in id_list)

    client = bigquery.Client(project="advertising-data-mart")
    query = f"""
    SELECT
      program_id,
      mars_segment_legacy,
      marketing_segment_rollup,
      COUNT(*) AS leads
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE inquiry_date >= '{PRIMARY_START}'
      AND inquiry_date < '{PRIMARY_END}'
      AND program_id IN ({id_sql})
    GROUP BY program_id, mars_segment_legacy, marketing_segment_rollup
    """
    seg_by_program: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in client.query(query).result():
        if should_skip_segment(row.marketing_segment_rollup):
            continue
        segment1 = resolve_segment1(
            row.mars_segment_legacy, row.marketing_segment_rollup
        )
        if not segment1:
            continue
        seg_by_program[row.program_id][segment1] += int(row.leads)

    programs_out: dict[str, dict] = {}
    for pid in id_list:
        segments = []
        seg_counts = seg_by_program.get(pid, {})
        for name in SEGMENT1_ORDER:
            if seg_counts.get(name, 0) > 0:
                segments.append({"segment": name, "leads": seg_counts[name]})
        f = funnel.get(pid, {})
        programs_out[pid] = {
            "segments": segments,
            "funnel": {
                "inquiries": f.get("inquiries", 0),
                "app_starts": f.get("app_starts", 0),
                "app_submits": f.get("app_submits", 0),
                "decisions": f.get("decisions", 0),
                "enrollments": f.get("enrollments", 0),
            },
        }

    OUT_PATH.write_text(
        json.dumps(
            {
                "generated": str(date.today()),
                "window": PRIMARY_LABEL,
                "segment1_order": SEGMENT1_ORDER,
                "programs": programs_out,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {OUT_PATH} ({len(programs_out)} programs)")


if __name__ == "__main__":
    main()
