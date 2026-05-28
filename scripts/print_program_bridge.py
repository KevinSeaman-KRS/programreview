"""Print bridge mapping table for review."""
import json
from pathlib import Path

programs = json.loads(
    (Path(__file__).parents[1] / "data" / "program_srm_bridge.json").read_text()
)["programs"]

print(f"{'lead_program_name':<52} {'SRM degree':<18} {'SRM major':<45} n3yr")
print("-" * 130)
for p in sorted(programs, key=lambda x: (x["degree_level"] or "", x.get("lead_program_name") or "")):
    lead = (p.get("lead_program_name") or p["full_program_name"])[:50]
    print(
        f"{lead:<52} {p['srm_degreelevel']:<18} {p['srm_majorname']:<45} "
        f"{p.get('srm_student_count_3yr', 0):>5}  {p['match_method']}"
    )
