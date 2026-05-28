"""Create dbo.program_srm_bridge table (DDL only). Populate with build_program_bridge.py."""
from pathlib import Path

import pymssql

ROOT = Path(__file__).resolve().parents[1]
ddl = (ROOT / "sql" / "create_program_srm_bridge.sql").read_text(encoding="utf-8")

conn = pymssql.connect(server="prodedlsql02", database="marketingsandbox")
cur = conn.cursor()
for batch in ddl.split("GO"):
    stmt = batch.strip()
    if stmt:
        cur.execute(stmt)
conn.commit()
conn.close()
print("Created dbo.program_srm_bridge — run: uvx --with pymssql python scripts/build_program_bridge.py")
