"""
Build bridge: vw_program (59 marketing programs) <-> StudentRevenueMaster major/degree.

Outputs:
  - data/program_srm_bridge.json
  - data/program_srm_bridge.csv
  - docs/program_srm_bridge_notes.md (unmapped / ambiguous)
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import pymssql

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "program_migration.json"
OUT_JSON = ROOT / "data" / "program_srm_bridge.json"
OUT_CSV = ROOT / "data" / "program_srm_bridge.csv"
OUT_NOTES = ROOT / "docs" / "program_srm_bridge_notes.md"

# degree_type on vw_program -> StudentRevenueMaster degreelevel label
DEGREE_TYPE_TO_SRM: dict[str, str] = {
    "Associates": "Associate",
    "Bachelors": "Bachelor",
    "Masters": "Master",
    "Doctoral": "Doctorate",
    "Post-Baccalaureate": "Graduate Certificate",
}

# Manual overrides: program_id -> (srm_degreelevel, srm_majorname)
MANUAL_BY_PROGRAM_ID: dict[str, tuple[str, str]] = {
    "001Vr00000YtotRIAR": (
        "Doctorate",
        "Organizational Development and Leadership",
    ),
    "001Vr00000t9K7vIAE": ("Master", "Leadership"),
    "001Do00000ScUzOIAV": ("Graduate Certificate", "Post Bacc_Elementary"),
    "001Do00000ScUyZIAV": ("Master", "Accounting"),  # Master of Accountancy
}

# full_program_name stem -> SRM MajorName when auto-parse fails
MANUAL_MAJOR_BY_FULL_NAME: dict[str, str] = {
    "Bachelor of Science in Nursing": "Nursing",
    "Bachelor of Science in Cyber & Data Security Technology": "Cyber and Data Security Technology",
    "Bachelor of Science in Information Technology": "Information Technology",
    "Bachelor of Science in Health Information Management": "Health Information Management",
    "Bachelor of Arts in Early Childhood Development with Differentiated Instruction": (
        "Early Childhood Development with Differentiated Instruction"
    ),
    "Bachelor of Arts in Operations Management & Analysis": "Operations Management and Analysis",
    "Bachelor of Arts in Health & Human Services": "Health and Human Services",
    "Master of Accountancy": "Accounting",
    "Master of Business Administration": "Business Administration",
    "Master of Arts in Early Childhood Education Leadership": "Early Childhood Education Leadership",
    "Master of Arts in Education": "Education",
    "Master of Arts in Health Care Administration": "Health Care Administration",
    "Master of Arts in Human Services": "Human Services",
    "Master of Arts in Organizational Management": "Organizational Management",
    "Master of Arts in Psychology": "Psychology",
    "Master of Science in Criminal Justice": "Criminal Justice",
    "Master of Science in Health Informatics and Analytics": "Health Informatics and Analytics",
    "Master of Science in Information Technology Management": "Information Technology Management",
    "Master of Science in Instructional Design and Technology": "Instructional Design and Technology",
    "Master of Science in Nursing": "Nursing",
    "Doctor of Professional Studies in Organizational Leadership": "Organizational Leadership",
    "Master of Professional Studies in Leadership": "Leadership",
    "Post Baccalaureate Teaching Certificate - Elementary Education": "Elementary Education",
}


def load_report_program_ids() -> list[str]:
    data = json.loads(MIGRATION_PATH.read_text(encoding="utf-8"))
    if isinstance(data.get("programs"), dict):
        return sorted(data["programs"].keys())
    return sorted(k for k in data.keys() if k.startswith("001"))


def extract_major_from_full_name(full_name: str, degree_type: str) -> str:
    if full_name in MANUAL_MAJOR_BY_FULL_NAME:
        return MANUAL_MAJOR_BY_FULL_NAME[full_name]

    name = full_name.strip()
    # "X in Y" / "X of Y in Z"
    m = re.search(r"\bin\s+(.+)$", name, re.I)
    if m:
        return m.group(1).strip()

    # "Master of Business Administration"
    m = re.search(r"^(?:Associate|Bachelor|Master|Doctor)\s+of\s+(.+)$", name, re.I)
    if m:
        return m.group(1).strip()

    # "Post Baccalaureate Teaching Certificate - Elementary Education"
    if " - " in name:
        return name.split(" - ", 1)[-1].strip()

    # AA in Business style from marketing names (if ever stored in full_program_name)
    m = re.search(r"^(?:AA|BA|BS|MA|MS|MBA|MACC|DPS)\s+in\s+(.+)$", name, re.I)
    if m:
        return m.group(1).strip()

    return name


def normalize_major_for_match(major: str) -> str:
    s = major.lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def fetch_vw_programs(cur, program_ids: list[str]) -> list[dict]:
    placeholders = ",".join(["%s"] * len(program_ids))
    cur.execute(
        f"""
        SELECT program_id, full_program_name, degree_level, degree_type,
               program_code_cvue, account_group, is_enrolling, is_active
        FROM dbo.vw_program
        WHERE program_id IN ({placeholders})
        ORDER BY degree_level, full_program_name
        """,
        tuple(program_ids),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_srm_combos(cur) -> list[dict]:
    cur.execute(
        """
        SELECT degreelevel AS srm_degreelevel,
               majorname AS srm_majorname,
               COUNT(*) AS student_count
        FROM dbo.StudentRevenueMaster
        WHERE MATRICDATE >= DATEADD(year, -3, GETDATE())
          AND majorname IS NOT NULL
          AND degreelevel IS NOT NULL
        GROUP BY degreelevel, majorname
        """
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_lead_program_names(cur, program_ids: list[str]) -> dict[str, str]:
    """Marketing program_name from lead cube for each program_id."""
    placeholders = ",".join(["%s"] * len(program_ids))
    cur.execute(
        f"""
        SELECT program_id,
               MAX(program_name) AS program_name,
               COUNT(*) AS lead_rows
        FROM dbo.vw_lead_extract_details
        WHERE program_id IN ({placeholders})
          AND inquiry_date >= DATEADD(month, -24, GETDATE())
        GROUP BY program_id
        """,
        tuple(program_ids),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def match_srm_major(
    parsed_major: str,
    srm_degree: str,
    srm_index: dict[tuple[str, str], dict],
) -> tuple[str | None, str, float]:
    """Return (matched_major, match_method, confidence 0-1)."""
    key_candidates = [
        (srm_degree, parsed_major),
    ]
    norm_parsed = normalize_major_for_match(parsed_major)

    # Exact case-insensitive
    for (deg, maj), rec in srm_index.items():
        if deg == srm_degree and maj.lower() == parsed_major.lower():
            return maj, "exact", 1.0

    # Normalized exact
    for (deg, maj), rec in srm_index.items():
        if deg == srm_degree and normalize_major_for_match(maj) == norm_parsed:
            return maj, "normalized", 0.95

    # Substring / contains
    best = None
    best_score = 0.0
    for (deg, maj), rec in srm_index.items():
        if deg != srm_degree:
            continue
        norm_maj = normalize_major_for_match(maj)
        if norm_parsed in norm_maj or norm_maj in norm_parsed:
            score = min(len(norm_parsed), len(norm_maj)) / max(len(norm_parsed), len(norm_maj))
            if score > best_score:
                best_score = score
                best = maj
    if best and best_score >= 0.55:
        return best, "fuzzy_contains", round(best_score, 2)

    return None, "unmatched", 0.0


def push_bridge_to_sql(cur, rows: list[dict]) -> None:
    cur.execute(
        """
        IF OBJECT_ID('dbo.program_srm_bridge', 'U') IS NULL
        BEGIN
            RAISERROR('Run sql/create_program_srm_bridge.sql first', 16, 1);
        END
        """
    )
    cur.execute("TRUNCATE TABLE dbo.program_srm_bridge")
    for r in rows:
        cur.execute(
            """
            INSERT INTO dbo.program_srm_bridge (
                program_id, full_program_name, lead_program_name,
                degree_level, degree_type, program_code_cvue, account_group,
                is_enrolling, srm_degreelevel, srm_majorname,
                match_method, match_confidence, srm_student_count_3yr
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["program_id"],
                r["full_program_name"],
                r.get("lead_program_name"),
                r.get("degree_level"),
                r.get("degree_type"),
                r.get("program_code_cvue"),
                r.get("account_group"),
                1 if r.get("is_enrolling") else 0,
                r["srm_degreelevel"],
                r["srm_majorname"],
                r["match_method"],
                r["match_confidence"],
                r.get("srm_student_count_3yr"),
            ),
        )


def validate_counts(cur, degree: str, major: str) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM dbo.StudentRevenueMaster
        WHERE degreelevel = %s AND majorname = %s
          AND MATRICDATE >= DATEADD(year, -3, GETDATE())
        """,
        (degree, major),
    )
    return int(cur.fetchone()[0])


def main() -> None:
    program_ids = load_report_program_ids()
    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor()

    vw = fetch_vw_programs(cur, program_ids)
    srm_combos = fetch_srm_combos(cur)
    lead_names = fetch_lead_program_names(cur, program_ids)

    srm_index: dict[tuple[str, str], dict] = {}
    for row in srm_combos:
        srm_index[(row["srm_degreelevel"], row["srm_majorname"])] = row

    bridge_rows: list[dict] = []
    unmatched: list[dict] = []
    ambiguous: list[dict] = []

    for p in vw:
        pid = p["program_id"]
        full_name = p["full_program_name"]
        dtype = p["degree_type"] or ""
        srm_degree = DEGREE_TYPE_TO_SRM.get(dtype)
        if pid in MANUAL_BY_PROGRAM_ID:
            srm_degree, srm_major = MANUAL_BY_PROGRAM_ID[pid]
            method, conf = "manual_program_id", 1.0
        else:
            parsed = extract_major_from_full_name(full_name, dtype)
            if not srm_degree:
                srm_major, method, conf = None, "no_degree_map", 0.0
                parsed = parsed
            else:
                srm_major, method, conf = match_srm_major(parsed, srm_degree, srm_index)
                parsed = parsed

        if srm_major and srm_degree:
            validated = validate_counts(cur, srm_degree, srm_major)
        else:
            validated = 0

        row = {
            "program_id": pid,
            "full_program_name": full_name,
            "lead_program_name": lead_names.get(pid),
            "degree_level": p["degree_level"],
            "degree_type": dtype,
            "program_code_cvue": p["program_code_cvue"],
            "account_group": p["account_group"],
            "is_enrolling": bool(p["is_enrolling"]),
            "parsed_major_stem": extract_major_from_full_name(full_name, dtype)
            if pid not in MANUAL_BY_PROGRAM_ID
            else None,
            "srm_degreelevel": srm_degree,
            "srm_majorname": srm_major,
            "match_method": method,
            "match_confidence": conf,
            "srm_student_count_3yr": validated,
        }
        bridge_rows.append(row)
        if not srm_major or conf < 0.9:
            (unmatched if not srm_major else ambiguous).append(row)

    # SRM combos not covered by any bridge row
    mapped_pairs = {
        (r["srm_degreelevel"], r["srm_majorname"])
        for r in bridge_rows
        if r["srm_degreelevel"] and r["srm_majorname"]
    }
    orphan_srm = [
        c
        for c in srm_combos
        if (c["srm_degreelevel"], c["srm_majorname"]) not in mapped_pairs
        and c["srm_degreelevel"] not in ("NDS",)
    ]

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_note": "Maps 59 report program_ids to StudentRevenueMaster degreelevel+majorname",
        "srm_matric_window": "MATRICDATE >= 3 years",
        "programs": bridge_rows,
        "unmatched_programs": [r["program_id"] for r in unmatched],
        "low_confidence_programs": [r["program_id"] for r in ambiguous],
        "srm_combos_not_in_bridge": orphan_srm[:30],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    fieldnames = list(bridge_rows[0].keys()) if bridge_rows else []
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(bridge_rows)

    lines = [
        "# Program ↔ StudentRevenueMaster bridge",
        "",
        f"- **Programs mapped:** {len(bridge_rows)}",
        f"- **Unmatched:** {len(unmatched)}",
        f"- **Low confidence (<0.9):** {len(ambiguous)}",
        f"- **SRM combos (3yr) not linked to a report program:** {len(orphan_srm)}",
        "",
        "## Unmatched",
        "",
    ]
    for r in unmatched:
        lines.append(
            f"- `{r['program_id']}` {r['full_program_name']} "
            f"(parsed: {r.get('parsed_major_stem')}, degree: {r['srm_degreelevel']})"
        )
    lines.extend(["", "## Low confidence", ""])
    for r in ambiguous:
        lines.append(
            f"- `{r['program_id']}` → {r['srm_degreelevel']} / {r['srm_majorname']} "
            f"({r['match_method']}, {r['match_confidence']})"
        )
    OUT_NOTES.write_text("\n".join(lines), encoding="utf-8")

    # Optional: upsert into SQL Server (requires CREATE TABLE from sql/create_program_srm_bridge.sql)
    try:
        push_bridge_to_sql(cur, bridge_rows)
        conn.commit()
        print("Upserted into dbo.program_srm_bridge")
    except Exception as exc:
        print(f"SQL table upsert skipped ({exc})")

    conn.close()
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")
    print(f"Unmatched: {len(unmatched)}, low confidence: {len(ambiguous)}")


if __name__ == "__main__":
    main()
