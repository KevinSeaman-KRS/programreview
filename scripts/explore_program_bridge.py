"""Explore vw_program vs StudentRevenueMaster for bridge mapping."""
import pymssql

conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
cur = conn.cursor()

cur.execute(
    """
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'vw_program' ORDER BY ORDINAL_POSITION
    """
)
print("vw_program columns:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT COUNT(*) FROM dbo.vw_program WHERE is_enrolling = 1")
print("enrolling programs:", cur.fetchone()[0])

cur.execute(
    """
    SELECT program_id, full_program_name, degree_level, degree_type,
           program_code_cvue, account_group, is_enrolling, is_active
    FROM dbo.vw_program
    ORDER BY degree_level, full_program_name
    """
)
programs = cur.fetchall()
print(f"all vw_program rows: {len(programs)}")
enrolling = [p for p in programs if p[6]]
print(f"is_enrolling=1: {len(enrolling)}")
print("First 5 enrolling:")
for p in enrolling[:5]:
    print(" ", p)

cur.execute(
    """
    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'StudentRevenueMaster'
      AND (COLUMN_NAME LIKE '%major%' OR COLUMN_NAME LIKE '%degree%'
           OR COLUMN_NAME LIKE '%program%')
    ORDER BY ORDINAL_POSITION
    """
)
print("SRM program-related cols:", [r[0] for r in cur.fetchall()])

cur.execute(
    """
    SELECT degreelevel, majorname, COUNT(*) AS n
    FROM dbo.StudentRevenueMaster
    WHERE MATRICDATE > '2024-01-01' AND majorname IS NOT NULL
    GROUP BY degreelevel, majorname
    ORDER BY n DESC
    """
)
srm = cur.fetchall()
print(f"SRM distinct degreelevel+majorname (since 2024): {len(srm)}")
print("Top 20:")
for r in srm[:20]:
    print(f"  {r[2]:>6}  {r[0]!r:30}  {r[1]!r}")

for pattern in ("%student%", "%person%", "%contact%", "%sfid%", "%external%"):
    cur.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'vw_lead_extract_details'
          AND COLUMN_NAME LIKE %s
        ORDER BY COLUMN_NAME
        """,
        (pattern,),
    )
    cols = [r[0] for r in cur.fetchall()]
    if cols:
        print(f"lead cols LIKE {pattern}:", cols)

conn.close()
