"""
Pull inquiry <-> enrollment program migration (12 months) from BigQuery.

Two views per program (see sql-query skill):
  - enrollment_view: applied program anchor, is_new_enrollment_final = 1
  - lead_cohort_view: inquiry program anchor, 12-mo leads, sum(is_new_enrollment_final)
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from google.cloud import bigquery

from report_periods import PRIMARY_END, PRIMARY_LABEL, PRIMARY_START

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = DATA_DIR / "program_migration.json"

ENROLLING_PROGRAM_IDS = [
    "001Do00000ScUyCIAV",
    "001Do00000ScUzUIAV",
    "001Do00000ScUyvIAF",
    "001Do00000ScUyDIAV",
    "001Do00000ScUyPIAV",
    "001Do00000ScUzGIAV",
    "001Do00000ScUyQIAV",
    "001Do00000ScUyEIAV",
    "001Do00000ScUzHIAV",
    "001Do00000ScUyRIAV",
    "001Do00000ScUzdIAF",
    "001Do00000ScUysIAF",
    "001Do00000ScUzeIAF",
    "001Do00000ScUzfIAF",
    "001Do00000ScUzgIAF",
    "001Do00000ScUzhIAF",
    "001Do00000ScUySIAV",
    "001Do00000ScUzEIAV",
    "001Do00000ScUyeIAF",
    "001Do00000ScUybIAF",
    "001Do00000ScUz6IAF",
    "001Do00000ScUyXIAV",
    "001Do00000ScUzZIAV",
    "001Do00000ScUyqIAF",
    "001Do00000ScUyTIAV",
    "001Do00000ScUyUIAV",
    "001Do00000ScUyVIAV",
    "001Do00000ScUyWIAV",
    "001Do00000ScUzFIAV",
    "001Do00000ScUz7IAF",
    "001Do00000ScUyzIAF",
    "001Do00000ScUzCIAV",
    "001Do00000ScUyNIAV",
    "001Do00000ScUzIIAV",
    "001Do00000ScUzJIAV",
    "001Do00000ScUyaIAF",
    "001Do00000ScUzKIAV",
    "001Do00000ScUymIAF",
    "001Vr00000YtotRIAR",
    "001Do00000ScUzbIAF",
    "001Do00000ScUzcIAF",
    "001Do00000ScUynIAF",
    "001Do00000ScUzAIAV",
    "001Do00000ScUy8IAF",
    "001Do00000ScUz9IAF",
    "001Do00000ScUzSIAV",
    "001Do00000ScUzTIAV",
    "001Do00000ScUyZIAV",
    "001Do00000ScUy9IAF",
    "001Do00000ScUyAIAV",
    "001Do00000ScUzMIAV",
    "001Do00000ScUylIAF",
    "001Vr00000t9K7vIAE",
    "001Do00000ScUz8IAF",
    "001Do00000ScUyBIAV",
    "001Do00000ScUykIAF",
    "001Do00000ScUzQIAV",
    "001Do00000ScUzNIAV",
    "001Do00000ScUzOIAV",
]

ID_LIST_SQL = ", ".join(f"'{pid}'" for pid in ENROLLING_PROGRAM_IDS)

INQUIRY_BUCKET_SQL = """
  CASE
    WHEN program_name LIKE 'Undecided%' THEN 'Undecided'
    WHEN program_name IS NULL OR TRIM(program_name) = '' THEN '(Unknown)'
    ELSE program_name
  END
"""

DATE_WINDOW = (
    f"inquiry_date >= '{PRIMARY_START}' AND inquiry_date < '{PRIMARY_END}'"
)
LEVEL_MATCH = "degree_level = applied_degree_level"
FINAL_ENROLL = "IFNULL(is_new_enrollment_final, 0) = 1"

# Transferred-in rows: top N inquiry sources + "Other programs" bucket
INFLOW_TOP_N = 5
OUTFLOW_TOP_N = 3


def top_n_plus_other(
    counts: dict[str, int], limit: int = 3, other_label: str = "Other programs"
) -> list[dict]:
    items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    top = items[:limit]
    other = sum(c for _, c in items[limit:])
    rows = [{"name": name, "count": count} for name, count in top]
    if other > 0:
        rows.append({"name": other_label, "count": other, "is_other": True})
    return rows


def build_flow_rows(
    anchor_name: str,
    enrollments_in: int,
    same_path: int,
    inflow_counts: dict[str, int],
    outflow_counts: dict[str, int],
    pct_note_in: str,
    pct_note_out: str,
) -> list[dict]:
    rows: list[dict] = []
    rows.append(
        {
            "section": "same",
            "inquiry": anchor_name,
            "applied": anchor_name,
            "count": same_path,
            "pct": round(100 * same_path / enrollments_in, 1) if enrollments_in else 0,
            "pct_note": pct_note_in,
        }
    )
    for item in top_n_plus_other(inflow_counts, limit=INFLOW_TOP_N):
        rows.append(
            {
                "section": "in",
                "inquiry": item["name"],
                "applied": anchor_name,
                "count": item["count"],
                "pct": round(100 * item["count"] / enrollments_in, 1) if enrollments_in else 0,
                "pct_note": pct_note_in,
                "is_other": item.get("is_other", False),
            }
        )
    enrolling_inquirers = same_path + sum(outflow_counts.values())
    for item in top_n_plus_other(outflow_counts, limit=OUTFLOW_TOP_N):
        rows.append(
            {
                "section": "out",
                "inquiry": anchor_name,
                "applied": item["name"],
                "count": item["count"],
                "pct": round(100 * item["count"] / enrolling_inquirers, 1)
                if enrolling_inquirers
                else 0,
                "pct_note": pct_note_out,
                "is_other": item.get("is_other", False),
            }
        )
    return rows


def build_enrollment_view(
    anchor_id: str,
    anchor_name: str,
    enrollments_in: int,
    same_path: int,
    inflow_counts: dict[str, int],
    outflow_counts: dict[str, int],
) -> dict | None:
    if enrollments_in == 0:
        return None

    inflow_other = enrollments_in - same_path
    outflow_other = sum(outflow_counts.values())
    net = inflow_other - outflow_other

    return {
        "anchor": "applied_program",
        "enrollment_flag": "is_new_enrollment_final",
        "enrollments_in": enrollments_in,
        "same_path_enrollments": same_path,
        "inflow_from_other": inflow_other,
        "outflow_to_other": outflow_other,
        "net_migration": net,
        "net_pct_enrollments": round(100 * net / enrollments_in, 1) if enrollments_in else None,
        "net_pct_same_path_base": round(100 * net / same_path, 1) if same_path else None,
        "enrolling_inquirers": same_path + outflow_other,
        "flow_rows": build_flow_rows(
            anchor_name,
            enrollments_in,
            same_path,
            inflow_counts,
            outflow_counts,
            "of final enrollments in this program",
            "of this program's inquirers with a final enrollment",
        ),
    }


def build_lead_cohort_view(
    anchor_name: str,
    inquiry_leads: int,
    final_enrollments: int,
    enrolled_in_program: int,
    outflow_counts: dict[str, int],
) -> dict | None:
    if inquiry_leads == 0:
        return None

    enrolled_elsewhere = final_enrollments - enrolled_in_program
    rate = round(100 * final_enrollments / inquiry_leads, 2) if inquiry_leads else 0

    flow_rows: list[dict] = []
    flow_rows.append(
        {
            "section": "same",
            "inquiry": anchor_name,
            "applied": anchor_name,
            "count": enrolled_in_program,
            "pct": round(100 * enrolled_in_program / final_enrollments, 1)
            if final_enrollments
            else 0,
            "pct_note": "of final enrollments from this inquiry cohort",
        }
    )
    for item in top_n_plus_other(outflow_counts, limit=OUTFLOW_TOP_N):
        flow_rows.append(
            {
                "section": "out",
                "inquiry": anchor_name,
                "applied": item["name"],
                "count": item["count"],
                "pct": round(100 * item["count"] / final_enrollments, 1)
                if final_enrollments
                else 0,
                "pct_note": "of final enrollments from this inquiry cohort",
                "is_other": item.get("is_other", False),
            }
        )

    return {
        "anchor": "inquiry_program",
        "enrollment_flag": "is_new_enrollment_final",
        "inquiry_leads": inquiry_leads,
        "final_enrollments": final_enrollments,
        "enrollment_rate_pct": rate,
        "enrolled_in_program": enrolled_in_program,
        "enrolled_elsewhere": enrolled_elsewhere,
        "flow_rows": flow_rows,
    }


def main() -> None:
    client = bigquery.Client(project="advertising-data-mart")

    enrolled_filter = f"""
      {DATE_WINDOW}
      AND {FINAL_ENROLL}
      AND applied_program_id IS NOT NULL
      AND TRIM(applied_program_name) != ''
      AND {LEVEL_MATCH}
    """

    print("Enrollment view: final enrollments by applied program...")
    q_enr_summary = f"""
    SELECT
      applied_program_id,
      ANY_VALUE(applied_program_name) AS name,
      COUNT(*) AS enrollments_in,
      COUNTIF(program_id = applied_program_id) AS same_path
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE {enrolled_filter}
      AND applied_program_id IN ({ID_LIST_SQL})
    GROUP BY applied_program_id
    """
    enr_summary = {
        row.applied_program_id: {
            "name": row.name,
            "enrollments_in": row.enrollments_in,
            "same_path": row.same_path,
        }
        for row in client.query(q_enr_summary).result()
    }

    q_enr_inflow = f"""
    SELECT applied_program_id, {INQUIRY_BUCKET_SQL} AS inquiry_bucket, COUNT(*) AS n
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE {enrolled_filter}
      AND applied_program_id IN ({ID_LIST_SQL})
      AND (program_id IS NULL OR program_id != applied_program_id)
    GROUP BY 1, 2
    """
    enr_inflows: dict[str, dict[str, int]] = defaultdict(dict)
    for row in client.query(q_enr_inflow).result():
        enr_inflows[row.applied_program_id][row.inquiry_bucket] = row.n

    q_enr_outflow = f"""
    SELECT program_id AS anchor_id, applied_program_name AS applied_program, COUNT(*) AS n
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE {enrolled_filter}
      AND program_id IN ({ID_LIST_SQL})
      AND applied_program_id != program_id
    GROUP BY 1, 2
    """
    enr_outflows: dict[str, dict[str, int]] = defaultdict(dict)
    for row in client.query(q_enr_outflow).result():
        enr_outflows[row.anchor_id][row.applied_program] = row.n

    print("Lead cohort view: inquiry leads + final enrollments...")
    q_lead = f"""
    SELECT
      program_id,
      ANY_VALUE(program_name) AS name,
      COUNT(*) AS inquiry_leads,
      SUM(IFNULL(is_new_enrollment_final, 0)) AS final_enrollments,
      COUNTIF({FINAL_ENROLL} AND applied_program_id = program_id) AS enrolled_in_program
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE {DATE_WINDOW}
      AND program_id IN ({ID_LIST_SQL})
    GROUP BY program_id
    """
    lead_summary = {row.program_id: row for row in client.query(q_lead).result()}

    q_lead_outflow = f"""
    SELECT program_id AS anchor_id, applied_program_name AS applied_program, COUNT(*) AS n
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE {DATE_WINDOW}
      AND {FINAL_ENROLL}
      AND program_id IN ({ID_LIST_SQL})
      AND applied_program_id != program_id
      AND applied_program_id IS NOT NULL
      AND {LEVEL_MATCH}
    GROUP BY 1, 2
    """
    lead_outflows: dict[str, dict[str, int]] = defaultdict(dict)
    for row in client.query(q_lead_outflow).result():
        lead_outflows[row.anchor_id][row.applied_program] = row.n

    migration: dict[str, dict] = {}
    for pid in ENROLLING_PROGRAM_IDS:
        name = None
        ev = None
        lv = None

        es = enr_summary.get(pid)
        if es:
            name = es["name"]
            ev = build_enrollment_view(
                pid,
                es["name"],
                es["enrollments_in"],
                es["same_path"],
                enr_inflows.get(pid, {}),
                enr_outflows.get(pid, {}),
            )

        ls = lead_summary.get(pid)
        if ls:
            name = name or ls.name
            lv = build_lead_cohort_view(
                ls.name,
                ls.inquiry_leads,
                ls.final_enrollments,
                ls.enrolled_in_program,
                lead_outflows.get(pid, {}),
            )

        if ev or lv:
            migration[pid] = {
                "program_id": pid,
                "program_name": name,
                "enrollment_view": ev,
                "lead_cohort_view": lv,
            }

    payload = {
        "generated": str(date.today()),
        "window": PRIMARY_LABEL,
        "definitions": {
            "enrollment_view": (
                "Final enrollments (is_new_enrollment_final=1) grouped by applied program; "
                "inflow/outflow among enrollees."
            ),
            "lead_cohort_view": (
                "12-month inquiry cohort by inquiry program_id; "
                "enrollment_rate = sum(is_new_enrollment_final) / leads."
            ),
        },
        "programs": migration,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {len(migration)} programs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
