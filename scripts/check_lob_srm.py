import pymssql

conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
cur = conn.cursor()
cur.execute(
    """
    SELECT lineofbusiness, COUNT(*) n
    FROM dbo.StudentRevenueMaster
    WHERE MATRICDATE >= DATEADD(month, -12, GETDATE())
    GROUP BY lineofbusiness ORDER BY n DESC
    """
)
for r in cur.fetchall():
    print(r)
conn.close()
