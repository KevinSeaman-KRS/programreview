import pymssql

conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
cur = conn.cursor()
for term in [
    "Account",
    "Leadership",
    "Organizational",
    "Elementary",
    "Teaching",
    "Doctor",
    "Certificate",
    "Professional",
]:
    cur.execute(
        """
        SELECT degreelevel, majorname, COUNT(*) n
        FROM dbo.StudentRevenueMaster
        WHERE majorname LIKE %s
        GROUP BY degreelevel, majorname
        ORDER BY n DESC
        """,
        (f"%{term}%",),
    )
    rows = cur.fetchall()
    if rows:
        print(f"\n-- LIKE %{term}% --")
        for r in rows[:15]:
            print(f"  {r[2]:5}  {r[0]:12}  {r[1]}")

conn.close()
