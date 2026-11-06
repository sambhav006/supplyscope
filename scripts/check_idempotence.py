"""Verify deterministic data contents across a second rebuild; stop API first."""
import hashlib,json
import duckdb
from pipelines import build
from backend.analytics import ROOT
def hashes():
    with duckdb.connect(str(ROOT/"data/supplyscope.duckdb"),read_only=True) as c:
        tables=[r[0] for r in c.execute("SHOW TABLES").fetchall()]
        return {t:c.execute(f"SELECT sha256(string_agg(to_json(r), '' ORDER BY to_json(r))) FROM {t} r").fetchone()[0] for t in tables}
before=hashes();build.main();after=hashes()
mismatches=[t for t in before if before[t]!=after[t]]
assert not mismatches, f"Changed tables: {mismatches}"
(ROOT/"reports/idempotence.json").write_text(json.dumps({"passed":True,"table_count":len(before),"sha256":after},indent=2))
print(f"Idempotence verified: {len(before)} tables identical.")
