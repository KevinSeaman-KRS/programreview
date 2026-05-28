"""
Pull enrolled-student demographics per marketing program via program_srm_bridge.

Output: program_demographics.json (keyed by program_id + baselines)
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import pymssql

from report_demographics import profile_rows
from report_periods import (
    DEMOGRAPHICS_MATRIC_END,
    DEMOGRAPHICS_MATRIC_LABEL,
    DEMOGRAPHICS_MATRIC_START,
)
from report_regions import region_distribution

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
BRIDGE_PATH = ROOT / "data" / "program_srm_bridge.json"
OUT_PATH = ROOT / "program_demographics.json"

UNDERGRAD_SRM = frozenset({"Associate", "Bachelor"})
GRAD_SRM = frozenset({"Master", "Doctorate", "Graduate Certificate"})


def load_bridge() -> list[dict]:
    data = json.loads(BRIDGE_PATH.read_text(encoding="utf-8"))
    return data["programs"]


def fetch_enrolled_by_program(cur) -> dict[str, list[dict]]:
    cur.execute(
        f"""
        SELECT b.program_id,
               s.race, s.gender, s.pell, s.maritalstatus, s.transferstatus,
               s.MilitaryFunding,
               s.age_at_matric, s.lineofbusiness, s.minority, s.state,
               s.degreelevel
        FROM dbo.StudentRevenueMaster s
        INNER JOIN dbo.program_srm_bridge b
          ON s.degreelevel = b.srm_degreelevel
         AND s.majorname = b.srm_majorname
        WHERE s.MATRICDATE >= %s AND s.MATRICDATE < %s
        """,
        (DEMOGRAPHICS_MATRIC_START, DEMOGRAPHICS_MATRIC_END),
    )
    cols = [d[0] for d in cur.description]
    by_program: dict[str, list[dict]] = {}
    for row in cur.fetchall():
        rec = dict(zip(cols, row))
        pid = rec.pop("program_id")
        by_program.setdefault(pid, []).append(rec)
    return by_program


def fetch_all_enrolled(cur) -> list[dict]:
    cur.execute(
        f"""
        SELECT race, gender, pell, maritalstatus, transferstatus,
               MilitaryFunding,
               age_at_matric, lineofbusiness, minority, state, degreelevel
        FROM dbo.StudentRevenueMaster
        WHERE MATRICDATE >= %s AND MATRICDATE < %s
        """,
        (DEMOGRAPHICS_MATRIC_START, DEMOGRAPHICS_MATRIC_END),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> None:
    if not BRIDGE_PATH.exists():
        raise FileNotFoundError(f"Run scripts/build_program_bridge.py first: {BRIDGE_PATH}")

    bridge = load_bridge()
    program_ids = [b["program_id"] for b in bridge]

    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor()

    logger.info("Fetching enrolled students by program...")
    by_program = fetch_enrolled_by_program(cur)
    all_rows = fetch_all_enrolled(cur)
    conn.close()

    undergrad_rows = [r for r in all_rows if r.get("degreelevel") in UNDERGRAD_SRM]
    grad_rows = [r for r in all_rows if r.get("degreelevel") in GRAD_SRM]

    baselines = {
        "all": profile_rows(all_rows, "All enrolled (12 mo matric)", graduate=False),
        "undergraduate": profile_rows(
            undergrad_rows, "Undergraduate enrolled", graduate=False
        ),
        "graduate": profile_rows(grad_rows, "Graduate enrolled", graduate=True),
    }

    programs_out: dict[str, dict] = {}
    for b in bridge:
        pid = b["program_id"]
        rows = by_program.get(pid, [])
        is_grad = b.get("srm_degreelevel") in GRAD_SRM
        prof = profile_rows(
            rows,
            b.get("lead_program_name") or b["full_program_name"],
            graduate=is_grad,
        )
        if prof:
            prof["srm_degreelevel"] = b["srm_degreelevel"]
            prof["srm_majorname"] = b["srm_majorname"]
            prof["regions"] = region_distribution(rows, min_pct=5.0)
        programs_out[pid] = prof

    all_regions = region_distribution(all_rows, min_pct=3.0)
    ug_regions = region_distribution(undergrad_rows, min_pct=3.0)
    grad_regions = region_distribution(grad_rows, min_pct=3.0)
    baselines["all_regions"] = all_regions
    baselines["undergraduate_regions"] = ug_regions
    baselines["graduate_regions"] = grad_regions

    payload = {
        "generated": str(date.today()),
        "matric_window": {
            "start": DEMOGRAPHICS_MATRIC_START,
            "end": DEMOGRAPHICS_MATRIC_END,
            "label": DEMOGRAPHICS_MATRIC_LABEL,
        },
        "source": "dbo.StudentRevenueMaster via dbo.program_srm_bridge",
        "baselines": baselines,
        "programs": programs_out,
        "summary": {
            "programs_with_students": sum(1 for p in programs_out.values() if p and p["count"] > 0),
            "total_students_mapped": sum(p["count"] for p in programs_out.values() if p),
        },
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {OUT_PATH}")
    print(f"  Programs with students: {payload['summary']['programs_with_students']}/{len(program_ids)}")
    print(f"  Total enrolled (mapped): {payload['summary']['total_students_mapped']:,}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
