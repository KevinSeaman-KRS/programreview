"""
Pull per-program widgets for detail pages:
  1) marketing_segment_rollup — % leads & % final enrollments (BigQuery)
  2) enrollment line of business — Core, FTG, Tuition Benefit, Military (SRM + bridge,
     PRIMARY YoY window; SRM matric aligned to same Jul–Jun window)
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

import pymssql
from google.cloud import bigquery

from marketing_segment_hierarchy import (
    MARKETING_ROLLUP_COLORS,
    MARKETING_ROLLUP_ORDER,
    SEGMENT1_COLORS,
    SEGMENT1_ORDER,
    SEGMENT_ROLLUP_COLORS,
    SEGMENT_ROLLUP_ORDER,
    resolve_marketing_levels,
    resolve_segment1,
)
from report_periods import (
    DEMOGRAPHICS_MATRIC_END,
    DEMOGRAPHICS_MATRIC_LABEL,
    DEMOGRAPHICS_MATRIC_START,
    PRIMARY_END,
    PRIMARY_LABEL,
    PRIMARY_START,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
MIGRATION_PATH = ROOT / "program_migration.json"
OUT_PATH = ROOT / "program_detail_widgets.json"

# SRM enrollment LOB — same 12-month matric window as enrolled-student profile
SRM_MATRIC_START = DEMOGRAPHICS_MATRIC_START
SRM_MATRIC_END = DEMOGRAPHICS_MATRIC_END
INQUIRY_START = PRIMARY_START
INQUIRY_END = PRIMARY_END

LOB_ORDER = ["Core", "Full Tuition Grant", "Tuition Benefit", "Military"]

LOB_COLORS = {
    "Core": "#0C234B",
    "Full Tuition Grant": "#AB0520",
    "Tuition Benefit": "#0076A8",
    "Military": "#98A4AE",
}

SKIP_SEGMENT_RE = re.compile(r"^(unknown|other|\(unknown\)|\(null\))$", re.I)


def load_program_ids() -> list[str]:
    data = json.loads(MIGRATION_PATH.read_text(encoding="utf-8"))
    return sorted(data["programs"].keys())


def should_skip_segment(segment: str | None) -> bool:
    if segment is None:
        return True
    s = str(segment).strip()
    if not s:
        return True
    return bool(SKIP_SEGMENT_RE.match(s))


def normalize_lob(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    if s in ("Core/Other", "Core"):
        return "Core"
    if s in LOB_ORDER:
        return s
    return None


def pct_distribution(
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


def fetch_segment_mix(client: bigquery.Client, program_ids: list[str]) -> dict[str, dict]:
    id_list = ", ".join(f"'{pid}'" for pid in program_ids)
    query = f"""
    SELECT
      program_id,
      mars_segment_legacy,
      marketing_segment_rollup,
      COUNT(*) AS leads,
      SUM(IFNULL(is_new_enrollment_final, 0)) AS enrollments
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE inquiry_date >= '{INQUIRY_START}'
      AND inquiry_date < '{INQUIRY_END}'
      AND program_id IN ({id_list})
    GROUP BY program_id, mars_segment_legacy, marketing_segment_rollup
    """
    by_program: dict[str, dict[str, dict[str, dict[str, int]]]] = defaultdict(
        lambda: {
            "rollup_leads": defaultdict(int),
            "rollup_enrollments": defaultdict(int),
            "segment_leads": defaultdict(int),
            "segment_enrollments": defaultdict(int),
            "paid_leads": defaultdict(int),
            "paid_enrollments": defaultdict(int),
        }
    )
    for row in client.query(query).result():
        if should_skip_segment(row.marketing_segment_rollup):
            continue
        resolved = resolve_marketing_levels(
            row.mars_segment_legacy, row.marketing_segment_rollup
        )
        if not resolved:
            continue
        marketing_rollup, segment_rollup = resolved
        pid = row.program_id
        leads = int(row.leads)
        enr = int(row.enrollments)
        by_program[pid]["rollup_leads"][marketing_rollup] += leads
        by_program[pid]["rollup_enrollments"][marketing_rollup] += enr
        by_program[pid]["segment_leads"][segment_rollup] += leads
        by_program[pid]["segment_enrollments"][segment_rollup] += enr
        if marketing_rollup == "Paid":
            segment1 = resolve_segment1(
                row.mars_segment_legacy, row.marketing_segment_rollup
            )
            if segment1:
                by_program[pid]["paid_leads"][segment1] += leads
                by_program[pid]["paid_enrollments"][segment1] += enr

    out: dict[str, dict] = {}
    for pid, buckets in by_program.items():
        lead_rows, lead_total = pct_distribution(
            dict(buckets["segment_leads"]), SEGMENT_ROLLUP_ORDER
        )
        enr_rows, enr_total = pct_distribution(
            dict(buckets["segment_enrollments"]), SEGMENT_ROLLUP_ORDER
        )
        rollup_lead_rows, rollup_lead_total = pct_distribution(
            dict(buckets["rollup_leads"]), MARKETING_ROLLUP_ORDER
        )
        rollup_enr_rows, rollup_enr_total = pct_distribution(
            dict(buckets["rollup_enrollments"]), MARKETING_ROLLUP_ORDER
        )
        paid_lead_rows, paid_lead_total = pct_distribution(
            dict(buckets["paid_leads"]), SEGMENT1_ORDER
        )
        paid_enr_rows, paid_enr_total = pct_distribution(
            dict(buckets["paid_enrollments"]), SEGMENT1_ORDER
        )
        out[pid] = {
            "leads": lead_rows,
            "leads_total": lead_total,
            "enrollments": enr_rows,
            "enrollments_total": enr_total,
            "rollup_leads": rollup_lead_rows,
            "rollup_leads_total": rollup_lead_total,
            "rollup_enrollments": rollup_enr_rows,
            "rollup_enrollments_total": rollup_enr_total,
            "paid_leads_breakdown": paid_lead_rows,
            "paid_leads_total": paid_lead_total,
            "paid_enrollment_breakdown": paid_enr_rows,
            "paid_enrollments_total": paid_enr_total,
        }
    return out


def fetch_enrollment_lob(program_ids: list[str]) -> dict[str, dict]:
    placeholders = ",".join(["%s"] * len(program_ids))
    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT b.program_id, s.lineofbusiness, COUNT(*) AS n
        FROM dbo.StudentRevenueMaster s
        INNER JOIN dbo.program_srm_bridge b
          ON s.degreelevel = b.srm_degreelevel AND s.majorname = b.srm_majorname
        WHERE s.MATRICDATE >= %s AND s.MATRICDATE < %s
          AND b.program_id IN ({placeholders})
        GROUP BY b.program_id, s.lineofbusiness
        """,
        (SRM_MATRIC_START, SRM_MATRIC_END, *program_ids),
    )
    raw: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pid, lob, n in cur.fetchall():
        bucket = normalize_lob(lob)
        if bucket:
            raw[pid][bucket] += int(n)
    conn.close()

    out: dict[str, dict] = {}
    for pid in program_ids:
        rows, total = pct_distribution(dict(raw.get(pid, {})), LOB_ORDER)
        out[pid] = {"buckets": rows, "total": total}
    return out


def main() -> None:
    program_ids = load_program_ids()
    client = bigquery.Client(project="advertising-data-mart")

    logger.info("Pulling marketing_segment_rollup mix...")
    segments = fetch_segment_mix(client, program_ids)

    logger.info("Pulling enrollment line of business...")
    lob = fetch_enrollment_lob(program_ids)

    programs_out: dict[str, dict] = {}
    for pid in program_ids:
        programs_out[pid] = {
            "marketing_segment": segments.get(
                pid,
                {
                    "leads": [],
                    "leads_total": 0,
                    "enrollments": [],
                    "enrollments_total": 0,
                },
            ),
            "enrollment_lob": lob.get(pid, {"buckets": [], "total": 0}),
        }

    payload = {
        "generated": str(date.today()),
        "window": PRIMARY_LABEL,
        "inquiry_window": {"start": INQUIRY_START, "end": INQUIRY_END},
        "matric_window": {
            "start": SRM_MATRIC_START,
            "end": SRM_MATRIC_END,
            "label": DEMOGRAPHICS_MATRIC_LABEL,
        },
        "marketing_rollup_order": MARKETING_ROLLUP_ORDER,
        "marketing_rollup_colors": MARKETING_ROLLUP_COLORS,
        "segment_order": SEGMENT_ROLLUP_ORDER,
        "segment_colors": SEGMENT_ROLLUP_COLORS,
        "segment1_order": SEGMENT1_ORDER,
        "segment1_colors": SEGMENT1_COLORS,
        "lob_order": LOB_ORDER,
        "lob_colors": LOB_COLORS,
        "enrollment_flag": "is_new_enrollment_final",
        "programs": programs_out,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with_seg = sum(
        1 for p in programs_out.values() if p["marketing_segment"]["leads_total"] > 0
    )
    with_lob = sum(1 for p in programs_out.values() if p["enrollment_lob"]["total"] > 0)
    print(f"Saved {OUT_PATH}")
    print(f"  Programs with segment data: {with_seg}/{len(program_ids)}")
    print(f"  Programs with LOB enroll data: {with_lob}/{len(program_ids)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
