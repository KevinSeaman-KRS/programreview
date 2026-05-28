"""Compare summary matrix programs vs vw_program / bridge."""
from __future__ import annotations

import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def from_bridge() -> list[dict]:
    data = json.loads((ROOT / "data" / "program_srm_bridge.json").read_text(encoding="utf-8"))
    return data["programs"]


def from_matrix() -> list[dict]:
    data = json.loads((ROOT / "program_data_full.json").read_text(encoding="utf-8"))
    return data["programs"]


def from_vw_program() -> list[dict]:
    import pymssql

    conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
    cur = conn.cursor(as_dict=True)
    cur.execute(
        """
        SELECT program_id, full_program_name, degree_level, degree_type,
               account_group, is_enrolling, is_active
        FROM dbo.vw_program
        ORDER BY is_enrolling DESC, degree_level, full_program_name
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def load_master_ids() -> set[str]:
    text = (ROOT / "pull_full_data.py").read_text(encoding="utf-8")
    start = text.index("MASTER_PROGRAM_IDS = [")
    end = text.index("]", start) + 1
    chunk = text[start:end].split("=", 1)[1].strip()
    ids: list[str] = []
    for line in chunk.splitlines():
        line = line.strip().strip(",").strip("[")
        if line.startswith('"'):
            ids.extend(
                part.strip().strip('"').strip("'")
                for part in line.split(",")
                if part.strip().strip('"').strip("'")
            )
    return set(ids)


def main() -> None:
    master = load_master_ids()

    matrix = from_matrix()
    matrix_ids = {p["program_id"] for p in matrix}
    bridge = from_bridge()
    bridge_ids = {p["program_id"] for p in bridge}
    print(f"Matrix rows: {len(matrix)}")
    print(f"MASTER_PROGRAM_IDS: {len(master)}")
    print(f"Bridge (vw_program snapshot): {len(bridge)}")

    try:
        vw = from_vw_program()
        vw_ids = {r["program_id"] for r in vw}
        vw_enrolling = [r for r in vw if r.get("is_enrolling")]
        print(f"vw_program live rows: {len(vw)}")
        print(f"vw_program is_enrolling=1: {len(vw_enrolling)}")
    except Exception as e:
        print(f"vw_program live query skipped: {e}")
        vw = None
        vw_ids = bridge_ids
        vw_enrolling = [p for p in bridge if p.get("is_enrolling")]

    source = vw if vw else bridge
    source_name = "vw_program" if vw else "program_srm_bridge.json"

    enrolling_src = [r for r in source if r.get("is_enrolling")]
    enrolling_ids = {r["program_id"] for r in enrolling_src}

    missing_from_matrix = [
        r for r in enrolling_src if r["program_id"] not in matrix_ids
    ]
    in_matrix_not_enrolling = [
        r for r in source
        if r["program_id"] in matrix_ids and not r.get("is_enrolling")
    ]
    in_vw_not_master = enrolling_ids - master
    master_not_in_vw_enrolling = master - enrolling_ids

    print(f"\n--- Enrolling in {source_name} but NOT in summary matrix ---")
    if not missing_from_matrix:
        print("  (none)")
    for r in sorted(
        missing_from_matrix,
        key=lambda x: (x.get("degree_level") or "", x.get("full_program_name") or ""),
    ):
        name = r.get("full_program_name") or r.get("program_name", "")
        print(
            f"  {r['program_id']}  {r.get('degree_level','?'):14}  "
            f"{r.get('account_group','—'):28}  {name}"
        )

    print(f"\n--- In matrix but {source_name} is_enrolling=0 ---")
    if not in_matrix_not_enrolling:
        print("  (none)")
    for r in sorted(
        in_matrix_not_enrolling,
        key=lambda x: x.get("full_program_name") or x.get("program_name") or "",
    ):
        name = r.get("full_program_name") or r.get("program_name", "")
        print(f"  {r['program_id']}  {name}")

    print(f"\n--- Enrolling in {source_name}, not in MASTER_PROGRAM_IDS ---")
    if not in_vw_not_master:
        print("  (none — matrix list matches enrolling vw set)")
    for pid in sorted(in_vw_not_master):
        r = next(x for x in enrolling_src if x["program_id"] == pid)
        print(f"  {pid}  {r.get('full_program_name','')}")

    print("\n--- MASTER_PROGRAM_IDS with is_enrolling=0 in vw ---")
    if not master_not_in_vw_enrolling:
        print("  (none)")
    for pid in sorted(master_not_in_vw_enrolling):
        r = next((x for x in source if x["program_id"] == pid), None)
        name = (r or {}).get("full_program_name", "(not in vw)")
        enr = (r or {}).get("is_enrolling")
        print(f"  {pid}  enrolling={enr}  {name}")

    # All vw rows not in matrix (including non-enrolling)
    all_missing = [r for r in source if r["program_id"] not in matrix_ids]
    non_enr_missing = [r for r in all_missing if not r.get("is_enrolling")]
    print(f"\n--- All {source_name} rows not in matrix (any is_enrolling) ---")
    print(
        f"  Total: {len(all_missing)} "
        f"({len(missing_from_matrix)} enrolling, {len(non_enr_missing)} non-enrolling)"
    )
    for r in sorted(
        non_enr_missing,
        key=lambda x: (x.get("degree_level") or "", x.get("full_program_name") or ""),
    ):
        active = r.get("is_active")
        print(
            f"  {r['program_id']}  active={active}  "
            f"{r.get('degree_level','?'):14}  {r.get('full_program_name','')}"
        )


if __name__ == "__main__":
    main()
    master = load_master_ids()
    matrix_ids = {p["program_id"] for p in from_matrix()}
    print("\n--- MASTER_PROGRAM_IDS not in program_data_full.json ---")
    for pid in sorted(master - matrix_ids):
        print(f"  {pid}")
