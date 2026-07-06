"""
Portfolio enrollment mix — year-over-year (Jul–Jun windows).

Outputs: portfolio_mix_yoy.json
  - BigQuery: enrollments & decisions by applied degree level (overall)
  - SRM: enrollment LOB mix (overall, undergraduate programs, graduate programs)
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date
from pathlib import Path

import pymssql
from google.cloud import bigquery

from program_master_fill import MASTER_PROGRAM_IDS
from report_periods import (
    PRIMARY_END,
    PRIMARY_LABEL,
    PRIMARY_START,
    PRIOR_END,
    PRIOR_LABEL,
    PRIOR_MATRIC_END,
    PRIOR_MATRIC_START,
    PRIOR_START,
)

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "portfolio_mix_yoy.json"

LOB_ORDER = ["Core", "Full Tuition Grant", "Tuition Benefit", "Military"]
UNDERGRAD_SRM = frozenset({"Associate", "Bachelor"})
GRAD_SRM = frozenset({"Master", "Doctorate", "Graduate Certificate"})
LEVEL_ORDER = ["Undergraduate", "Graduate"]


def normalize_lob(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    if s in ("Core/Other", "Core"):
        return "Core"
    if s in LOB_ORDER:
        return s
    return None


def pct_rows(counts: dict[str, int], order: list[str]) -> tuple[list[dict], int]:
    total = sum(counts.values())
    if total == 0:
        return [], 0
    rows = []
    for key in order:
        c = counts.get(key, 0)
        if c:
            rows.append({"label": key, "count": c, "pct": round(c / total * 100, 1)})
    return rows, total


def fetch_bq_level_mix(
    client: bigquery.Client,
    start: str,
    end: str,
    program_ids: list[str],
) -> dict[str, dict[str, int]]:
    id_list = ", ".join(f"'{pid}'" for pid in program_ids)
    query = f"""
    SELECT
      CASE
        WHEN applied_degree_level = 'Undergraduate' THEN 'Undergraduate'
        WHEN applied_degree_level = 'Graduate' THEN 'Graduate'
        ELSE 'Other'
      END AS level_bucket,
      SUM(is_appin) AS decisions,
      SUM(IFNULL(is_new_enrollment_final, 0)) AS enrollments
    FROM `advertising-data-mart.inquiries.vw_lead_extract_details`
    WHERE inquiry_date >= '{start}'
      AND inquiry_date < '{end}'
      AND program_id IN ({id_list})
    GROUP BY level_bucket
    """
    out: dict[str, dict[str, int]] = {
        "decisions": defaultdict(int),
        "enrollments": defaultdict(int),
    }
    for row in client.query(query).result():
        bucket = row.level_bucket
        if bucket == "Other":
            continue
        out["decisions"][bucket] = int(row.decisions or 0)
        out["enrollments"][bucket] = int(row.enrollments or 0)
    return {
        "decisions": dict(out["decisions"]),
        "enrollments": dict(out["enrollments"]),
    }


def fetch_srm_lob_mix(start: str, end: str, srm_levels: frozenset[str] | None) -> dict[str, int]:
    level_filter = ""
    params: list = [start, end]
    if srm_levels is not None:
        placeholders = ", ".join(["%s"] * len(srm_levels))
        level_filter = f" AND s.degreelevel IN ({placeholders})"
        params.extend(sorted(srm_levels))

    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT s.lineofbusiness, COUNT(*) AS n
        FROM dbo.StudentRevenueMaster s
        INNER JOIN dbo.program_srm_bridge b
          ON s.degreelevel = b.srm_degreelevel AND s.majorname = b.srm_majorname
        WHERE s.MATRICDATE >= %s AND s.MATRICDATE < %s
        {level_filter}
        GROUP BY s.lineofbusiness
        """,
        tuple(params),
    )
    counts: dict[str, int] = defaultdict(int)
    for lob, n in cur.fetchall():
        bucket = normalize_lob(lob)
        if bucket:
            counts[bucket] += int(n)
    conn.close()
    return dict(counts)


def build_slice(
    client: bigquery.Client,
    program_ids: list[str],
    srm_levels: frozenset[str] | None,
    label: str,
) -> dict:
    primary_bq = fetch_bq_level_mix(client, PRIMARY_START, PRIMARY_END, program_ids)
    prior_bq = fetch_bq_level_mix(client, PRIOR_START, PRIOR_END, program_ids)

    primary_lob_counts = fetch_srm_lob_mix(PRIMARY_START, PRIMARY_END, srm_levels)
    prior_lob_counts = fetch_srm_lob_mix(PRIOR_MATRIC_START, PRIOR_MATRIC_END, srm_levels)

    primary_lob_rows, primary_lob_total = pct_rows(primary_lob_counts, LOB_ORDER)
    prior_lob_rows, prior_lob_total = pct_rows(prior_lob_counts, LOB_ORDER)

    def level_pcts(enroll: dict[str, int]) -> list[dict]:
        rows, total = pct_rows(enroll, LEVEL_ORDER)
        return rows

    return {
        "label": label,
        "primary": {
            "window": PRIMARY_LABEL,
            "level_mix": {
                "decisions": level_pcts(primary_bq["decisions"]),
                "enrollments": level_pcts(primary_bq["enrollments"]),
            },
            "lob_enrollments": primary_lob_rows,
            "lob_total": primary_lob_total,
        },
        "prior": {
            "window": PRIOR_LABEL,
            "level_mix": {
                "decisions": level_pcts(prior_bq["decisions"]),
                "enrollments": level_pcts(prior_bq["enrollments"]),
            },
            "lob_enrollments": prior_lob_rows,
            "lob_total": prior_lob_total,
        },
    }


def main() -> None:
    client = bigquery.Client(project="advertising-data-mart")

    undergrad_ids = [
        pid
        for pid in MASTER_PROGRAM_IDS
        if pid  # filled from bridge at runtime if needed
    ]
    # Split by degree_level from bridge file when available
    bridge_path = ROOT / "data" / "program_srm_bridge.json"
    if bridge_path.exists():
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))["programs"]
        by_id = {p["program_id"]: p for p in bridge}
        undergrad_ids = [
            pid for pid in MASTER_PROGRAM_IDS if by_id.get(pid, {}).get("degree_level") == "Undergraduate"
        ]
        graduate_ids = [
            pid for pid in MASTER_PROGRAM_IDS if by_id.get(pid, {}).get("degree_level") == "Graduate"
        ]
    else:
        graduate_ids = list(MASTER_PROGRAM_IDS)

    logger.info("Pulling portfolio mix YoY slices...")
    payload = {
        "generated": str(date.today()),
        "primary_window": {"start": PRIMARY_START, "end": PRIMARY_END, "label": PRIMARY_LABEL},
        "prior_window": {"start": PRIOR_START, "end": PRIOR_END, "label": PRIOR_LABEL},
        "lob_order": LOB_ORDER,
        "slices": {
            "overall": build_slice(client, list(MASTER_PROGRAM_IDS), None, "Overall portfolio"),
            "undergraduate": build_slice(
                client, undergrad_ids, UNDERGRAD_SRM, "Undergraduate programs"
            ),
            "graduate": build_slice(
                client, graduate_ids, GRAD_SRM, "Graduate programs"
            ),
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
