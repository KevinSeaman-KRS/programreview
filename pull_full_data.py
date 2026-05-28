"""
Pull program metrics for fixed 6-month windows from BigQuery.
Outputs: program_data_full.json

Primary: Oct 2025 – Mar 2026 | Prior: Apr – Sep 2025
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from google.cloud import bigquery

from marketing_segment_hierarchy import navigational_legacy_sql_list
from program_master_fill import MASTER_PROGRAM_IDS, fill_missing_master_programs
from report_periods import (
    MONTHLY_DETAIL_END,
    MONTHLY_DETAIL_LABEL,
    MONTHLY_DETAIL_START,
    PRIMARY_END,
    PRIMARY_LABEL,
    PRIMARY_START,
    PRIOR_END,
    PRIOR_LABEL,
    PRIOR_START,
)

ROOT = Path(__file__).resolve().parent
client = bigquery.Client(project="advertising-data-mart")

id_list_sql = ", ".join(f"'{pid}'" for pid in MASTER_PROGRAM_IDS)
nav_legacy_sql = navigational_legacy_sql_list()

print(f"Pulling primary ({PRIMARY_LABEL}) vs prior ({PRIOR_LABEL})...")

query_totals = f"""
WITH primary_period AS (
    SELECT
        program_id,
        program_name,
        degree_level,
        degree_type,
        COUNT(*) AS leads,
        SUM(is_app_started) AS apps_started,
        SUM(IFNULL(is_app_submitted, 0)) AS apps_submitted,
        SUM(is_appin) AS decisions,
        SUM(IFNULL(is_new_enrollment_final, 0)) AS new_enrollments,
        SUM(
          CASE
            WHEN mars_segment_legacy IN ({nav_legacy_sql}) THEN 1
            WHEN mars_segment_legacy IS NULL
              AND marketing_segment_rollup IN ('Brand - Search', 'Organic') THEN 1
            ELSE 0
          END
        ) AS navigational_leads,
        SUM(
          CASE
            WHEN IFNULL(is_new_enrollment_final, 0) = 1
              AND (
                mars_segment_legacy IN ({nav_legacy_sql})
                OR (
                  mars_segment_legacy IS NULL
                  AND marketing_segment_rollup IN ('Brand - Search', 'Organic')
                )
              )
            THEN 1
            ELSE 0
          END
        ) AS navigational_enrollments
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE inquiry_date >= '{PRIMARY_START}'
      AND inquiry_date < '{PRIMARY_END}'
      AND program_id IN ({id_list_sql})
    GROUP BY program_id, program_name, degree_level, degree_type
),
prior_period AS (
    SELECT
        program_id,
        COUNT(*) AS py_leads,
        SUM(is_app_started) AS py_apps_started,
        SUM(IFNULL(is_app_submitted, 0)) AS py_apps_submitted,
        SUM(is_appin) AS py_decisions,
        SUM(IFNULL(is_new_enrollment_final, 0)) AS py_new_enrollments
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE inquiry_date >= '{PRIOR_START}'
      AND inquiry_date < '{PRIOR_END}'
      AND program_id IN ({id_list_sql})
    GROUP BY program_id
)
SELECT
    c.*,
    IFNULL(p.py_leads, 0) AS py_leads,
    IFNULL(p.py_apps_started, 0) AS py_apps_started,
    IFNULL(p.py_apps_submitted, 0) AS py_apps_submitted,
    IFNULL(p.py_decisions, 0) AS py_decisions,
    IFNULL(p.py_new_enrollments, 0) AS py_new_enrollments
FROM primary_period c
LEFT JOIN prior_period p ON c.program_id = p.program_id
ORDER BY c.leads DESC
"""

programs = []
for row in client.query(query_totals).result():
    nav_pct = (
        round(row.navigational_enrollments / row.new_enrollments * 100, 1)
        if row.new_enrollments
        else None
    )
    programs.append({
        "program_id": row.program_id,
        "program_name": row.program_name,
        "degree_level": row.degree_level,
        "degree_type": row.degree_type,
        "leads": row.leads,
        "apps_started": row.apps_started,
        "apps_submitted": row.apps_submitted,
        "decisions": row.decisions,
        "new_enrollments": row.new_enrollments,
        "pct_navigational": nav_pct,
        "py_leads": row.py_leads,
        "py_apps_started": row.py_apps_started,
        "py_apps_submitted": row.py_apps_submitted,
        "py_decisions": row.py_decisions,
        "py_new_enrollments": row.py_new_enrollments,
    })

n_pulled = len(programs)
programs = fill_missing_master_programs(programs, ROOT / "data" / "program_srm_bridge.json")
if len(programs) > n_pulled:
    print(f"  Zero-filled {len(programs) - n_pulled} master program(s) with no inquiry rows")
print(f"  Retrieved {len(programs)} programs")
print(f"  Primary leads: {sum(p['leads'] for p in programs):,}")
print(f"  Prior leads: {sum(p['py_leads'] for p in programs):,}")

print(f"\nPulling monthly breakdown ({MONTHLY_DETAIL_LABEL})...")
query_monthly = f"""
SELECT
    program_id,
    FORMAT_DATE('%Y-%m', inquiry_date) AS month,
    COUNT(*) AS leads,
    SUM(is_app_started) AS apps_started,
    SUM(IFNULL(is_app_submitted, 0)) AS apps_submitted,
    SUM(is_appin) AS decisions,
    SUM(IFNULL(is_new_enrollment_final, 0)) AS new_enrollments
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= '{MONTHLY_DETAIL_START}'
  AND inquiry_date < '{MONTHLY_DETAIL_END}'
  AND program_id IN ({id_list_sql})
GROUP BY program_id, month
ORDER BY program_id, month
"""
monthly: dict[str, list] = {}
for row in client.query(query_monthly).result():
    monthly.setdefault(row.program_id, []).append({
        "month": row.month,
        "leads": row.leads,
        "apps_started": row.apps_started,
        "apps_submitted": row.apps_submitted,
        "decisions": row.decisions,
        "new_enrollments": row.new_enrollments,
    })

print(f"  Monthly data for {len(monthly)} programs")

print("\nPulling funnel stage data (primary window)...")
query_funnel = f"""
SELECT
    program_id,
    COUNT(*) AS inquiries,
    SUM(is_app_started) AS app_starts,
    SUM(IFNULL(is_app_submitted, 0)) AS app_submits,
    SUM(is_appin) AS decisions,
    SUM(IFNULL(is_new_enrollment_final, 0)) AS enrollments
FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
WHERE inquiry_date >= '{PRIMARY_START}'
  AND inquiry_date < '{PRIMARY_END}'
  AND program_id IN ({id_list_sql})
GROUP BY program_id
"""
funnel = {
    row.program_id: {
        "inquiries": row.inquiries,
        "app_starts": row.app_starts,
        "app_submits": row.app_submits,
        "decisions": row.decisions,
        "enrollments": row.enrollments,
    }
    for row in client.query(query_funnel).result()
}

output = {
    "generated": str(date.today()),
    "primary_period": {"start": PRIMARY_START, "end": PRIMARY_END, "label": PRIMARY_LABEL},
    "prior_period": {"start": PRIOR_START, "end": PRIOR_END, "label": PRIOR_LABEL},
    "monthly_detail_period": {
        "start": MONTHLY_DETAIL_START,
        "end": MONTHLY_DETAIL_END,
        "label": MONTHLY_DETAIL_LABEL,
    },
    "programs": programs,
    "monthly": monthly,
    "funnel": funnel,
}

out_path = ROOT / "program_data_full.json"
out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"\nSaved {out_path}")
