"""Cross-check bridge using lead program_id vs SRM on shared student keys."""
import json
from collections import Counter
from pathlib import Path

import pymssql

ROOT = Path(__file__).resolve().parents[1]
bridge = {
    r["program_id"]: (r["srm_degreelevel"], r["srm_majorname"])
    for r in json.loads((ROOT / "data" / "program_srm_bridge.json").read_text())["programs"]
}

conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
cur = conn.cursor()
cur.execute(
    """
    SELECT TOP 5000
      l.program_id,
      l.program_name,
      s.degreelevel,
      s.majorname
    FROM dbo.vw_lead_extract_details l
    INNER JOIN dbo.StudentRevenueMaster s
      ON CAST(l.systudentid AS VARCHAR(32)) = CAST(s.systudentid AS VARCHAR(32))
    WHERE l.is_lead_cube_new_enrollment_final = 1
      AND l.inquiry_date >= DATEADD(month, -24, GETDATE())
      AND l.program_id IS NOT NULL
      AND s.majorname IS NOT NULL
    """
)
rows = cur.fetchall()
conn.close()

agree = 0
mismatch = Counter()
for program_id, program_name, deg, maj in rows:
    expected = bridge.get(program_id)
    if not expected:
        continue
    if (deg, maj) == expected:
        agree += 1
    else:
        mismatch[(program_id, program_name, expected, (deg, maj))] += 1

print(f"rows checked: {len(rows)}")
print(f"bridge agree: {agree}")
print(f"bridge mismatch rows: {sum(mismatch.values())}")
print("top mismatches:")
for key, n in mismatch.most_common(12):
    pid, pname, exp, actual = key
    print(f"  {n:4}  lead={pname!r}")
    print(f"        bridge={exp[0]}/{exp[1]!r}  srm={actual[0]}/{actual[1]!r}")
