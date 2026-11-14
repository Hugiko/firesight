import json
import os
import sqlite3
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("FIRESIGHT_DB", ROOT / "data" / "processed" / "firesight.db"))

NUMERIC = {"size_mm", "o2_pct", "pressure_kpa", "co2_pct", "he_pct", "flow_cm_s", "burn_time_s",
           "extinction_diameter_mm", "burning_rate", "adiabatic_temp_k"}


def connect():
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


@lru_cache(maxsize=1)
def store():
    con = connect()
    invs = [json.loads(r["data"]) for r in con.execute("SELECT data FROM investigations")]
    tests = []
    for r in con.execute("SELECT * FROM tests"):
        d = dict(r)
        d["ignited"] = None if d["ignited"] in (None, "None") else d["ignited"] == "True"
        tests.append(d)
    pubs = [json.loads(r["data"]) for r in con.execute("SELECT data FROM publications")]
    sims = [json.loads(r["data"]) for r in con.execute("SELECT data FROM similarity")]
    chunks = [dict(r) for r in con.execute("SELECT * FROM chunks ORDER BY id")]
    kv = {r["key"]: json.loads(r["value"]) for r in con.execute("SELECT key, value FROM kv")}
    con.close()
    return {"investigations": {i["id"]: i for i in invs}, "tests": tests, "publications": pubs,
            "similarity": sims, "chunks": chunks, "analytics": kv["analytics"], "meta": kv["meta"]}
