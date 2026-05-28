"""
Preview Pell, MilitaryFunding, Dependents, TransferStatus distributions
for enrolled-student profile (SRM matric window, program_srm_bridge).

Pell %: Core LOB only. Military funding %: Military LOB only.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pymssql

from report_periods import PRIMARY_END, PRIMARY_LABEL, PRIMARY_START

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "srm_profile_fields_preview.json"

CORE_LOB = frozenset({"Core", "Core/Other"})
MIL_LOB = frozenset({"Military"})


def normalize_lob(raw: str | None) -> str | None:
    if not raw:
        return None
    s = str(raw).strip()
    if s in CORE_LOB:
        return "Core"
    if s in MIL_LOB:
        return "Military"
    if s in ("Full Tuition Grant", "Tuition Benefit"):
        return s
    return s


def distribution(rows: list[dict], field: str, denominator_n: int | None = None) -> dict:
    n = denominator_n if denominator_n is not None else len(rows)
    if n == 0:
        return {"n": 0, "buckets": []}
    c = Counter(str(r[field]).strip() if r.get(field) is not None else "(null)" for r in rows)
    buckets = []
    for label, count in c.most_common():
        buckets.append({
            "label": label,
            "count": count,
            "pct": round(count / n * 100, 1),
        })
    return {"n": n, "buckets": buckets}


def pell_yes_pct(rows: list[dict]) -> float | None:
    if not rows:
        return None
    yes = sum(
        1
        for r in rows
        if str(r.get("pell") or "").strip().lower() in ("yes", "y", "pell")
    )
    return round(yes / len(rows) * 100, 1)


def fetch_rows(cur) -> list[dict]:
    cur.execute(
        """
        SELECT s.pell,
               s.MilitaryFunding,
               s.Dependents,
               s.TransferStatus,
               s.transferstatus,
               s.lineofbusiness,
               s.degreelevel,
               b.program_id,
               b.lead_program_name
        FROM dbo.StudentRevenueMaster s
        INNER JOIN dbo.program_srm_bridge b
          ON s.degreelevel = b.srm_degreelevel
         AND s.majorname = b.srm_majorname
        WHERE s.MATRICDATE >= %s AND s.MATRICDATE < %s
        """,
        (PRIMARY_START, PRIMARY_END),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def main() -> None:
    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor()
    rows = fetch_rows(cur)
    conn.close()

    for r in rows:
        r["lob_bucket"] = normalize_lob(r.get("lineofbusiness"))

    core_rows = [r for r in rows if r.get("lob_bucket") == "Core"]
    mil_rows = [r for r in rows if r.get("lob_bucket") == "Military"]

    transfer_field = "TransferStatus" if any(r.get("TransferStatus") is not None for r in rows) else "transferstatus"

    preview = {
        "matric_window": {"start": PRIMARY_START, "end": PRIMARY_END, "label": PRIMARY_LABEL},
        "total_enrolled_mapped": len(rows),
        "core_enrolled_n": len(core_rows),
        "military_enrolled_n": len(mil_rows),
        "rules": {
            "pell": "Distribution and Pell-yes % among Core LOB only",
            "military_funding": "Distribution among Military LOB only",
            "dependents": "All enrolled (mapped programs)",
            "transfer_status": "All enrolled (mapped programs)",
        },
        "all_enrolled": {
            "dependents": distribution(rows, "Dependents"),
            "transfer_status": distribution(rows, transfer_field),
            "pell_all_lob_warning": distribution(rows, "pell"),
        },
        "core_only": {
            "n": len(core_rows),
            "pell_distribution": distribution(core_rows, "pell"),
            "pell_yes_pct": pell_yes_pct(core_rows),
        },
        "military_only": {
            "n": len(mil_rows),
            "military_funding": distribution(mil_rows, "MilitaryFunding"),
        },
        "by_degreelevel": {},
        "sample_programs": {},
    }

    for level in sorted({r.get("degreelevel") for r in rows if r.get("degreelevel")}):
        sub = [r for r in rows if r.get("degreelevel") == level]
        sub_core = [r for r in sub if r.get("lob_bucket") == "Core"]
        sub_mil = [r for r in sub if r.get("lob_bucket") == "Military"]
        preview["by_degreelevel"][level] = {
            "n": len(sub),
            "core_n": len(sub_core),
            "military_n": len(sub_mil),
            "dependents": distribution(sub, "Dependents"),
            "transfer_status": distribution(sub, transfer_field),
            "core_pell_yes_pct": pell_yes_pct(sub_core),
            "core_pell_dist": distribution(sub_core, "pell") if sub_core else {"n": 0, "buckets": []},
            "mil_funding": distribution(sub_mil, "MilitaryFunding") if sub_mil else {"n": 0, "buckets": []},
        }

    by_pid: dict[str, list[dict]] = {}
    for r in rows:
        by_pid.setdefault(r["program_id"], []).append(r)

    samples = sorted(
        ((pid, rs) for pid, rs in by_pid.items() if len(rs) >= 15),
        key=lambda x: -len(x[1]),
    )[:6]
    for pid, rs in samples:
        name = rs[0].get("lead_program_name") or pid
        cr = [r for r in rs if r.get("lob_bucket") == "Core"]
        mr = [r for r in rs if r.get("lob_bucket") == "Military"]
        preview["sample_programs"][pid] = {
            "name": name,
            "n": len(rs),
            "core_n": len(cr),
            "military_n": len(mr),
            "dependents": distribution(rs, "Dependents"),
            "transfer_status": distribution(rs, transfer_field),
            "core_pell_yes_pct": pell_yes_pct(cr),
            "core_pell_dist": distribution(cr, "pell") if cr else {"n": 0, "buckets": []},
            "mil_funding": distribution(mr, "MilitaryFunding") if mr else {"n": 0, "buckets": []},
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(preview, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Enrolled mapped: {len(rows):,} | Core: {len(core_rows):,} | Military: {len(mil_rows):,}")
    print(f"Core Pell-yes %: {preview['core_only']['pell_yes_pct']}")
    print("Core Pell dist:", preview["core_only"]["pell_distribution"]["buckets"][:5])
    print("Mil funding:", preview["military_only"]["military_funding"]["buckets"][:6])


if __name__ == "__main__":
    main()
