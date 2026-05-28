"""Print bridge validation summary to stdout."""
import json
from pathlib import Path

payload = json.loads((Path(__file__).parents[1] / "data" / "program_srm_bridge.json").read_text())
programs = payload.get("programs", [])
print("programs:", len(programs))
zero = [p for p in programs if p.get("srm_student_count_3yr") == 0]
print("zero SRM count:", len(zero))
for p in zero:
    print(" ", p["full_program_name"], "->", p["srm_degreelevel"], p["srm_majorname"])
print("\nSample mappings:")
for p in programs[:5]:
    print(
        f"  {p['lead_program_name']!r:45} -> {p['srm_degreelevel']}/{p['srm_majorname']} "
        f"({p['match_method']}, n={p['srm_student_count_3yr']})"
    )
low = sorted(programs, key=lambda x: x.get("srm_student_count_3yr", 0))[:10]
print("\nLowest enrollment (3yr):")
for p in low:
    print(f"  {p['srm_student_count_3yr']:4}  {p['srm_degreelevel']:12} {p['srm_majorname']}")
