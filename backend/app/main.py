import csv
import io
import math
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assistant import LAST_LLM_ERROR, answer, llm_available
from .data import ROOT, store
from .search import search

app = FastAPI(title="FireSight API", version="1.0",
              description="NASA PSI combustion data for spacecraft and habitat fire safety.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.on_event("startup")
def _warm_up():
    """Load the database and build the search index in the background, so the first visitor does not wait."""
    import threading

    def work():
        try:
            store()
            search("fire oxygen", k=1)
        except Exception:
            pass
    threading.Thread(target=work, daemon=True).start()


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return resp

TEST_COLS = ["test_id", "investigation", "date", "fuel", "fuel_phase", "material_class", "geometry", "size_mm",
             "o2_pct", "pressure_kpa", "diluent", "co2_pct", "he_pct", "flow_cm_s", "flow_direction", "gravity",
             "ignited", "outcome", "burn_time_s", "extinction_diameter_mm", "burning_rate", "adiabatic_temp_k",
             "notes", "source", "confidence"]


@app.get("/api/health")
def health():
    s = store()
    return {"status": "ok", "investigations": len(s["investigations"]), "tests": len(s["tests"]),
            "llm": llm_available(), "llm_last_error": LAST_LLM_ERROR["error"]}


@app.get("/api/meta")
def meta():
    return store()["meta"]


@app.get("/api/investigations")
def investigations():
    return list(store()["investigations"].values())


@app.get("/api/investigations/{inv_id}")
def investigation(inv_id: str):
    s = store()
    inv = s["investigations"].get(inv_id)
    if not inv:
        raise HTTPException(404, "Unknown investigation")
    sims = sorted((x for x in s["similarity"] if inv_id in (x["a"], x["b"])), key=lambda x: -x["score"])[:5]
    return {**inv,
            "tests": [t for t in s["tests"] if t["investigation"] == inv_id],
            "reports": [p for p in s["publications"] if p["investigation"] == inv_id and p["relevance"] != "related"],
            "similar": [{"id": x["b"] if x["a"] == inv_id else x["a"], **x} for x in sims]}


def filter_tests(investigation=None, phase=None, o2_min=None, o2_max=None, p_min=None, p_max=None, fuel=None):
    out = []
    for t in store()["tests"]:
        if investigation and t["investigation"] not in investigation.split(","):
            continue
        if phase and t["fuel_phase"] != phase:
            continue
        if fuel and fuel.lower() not in (t["fuel"] or "").lower():
            continue
        o2, p = t["o2_pct"], t["pressure_kpa"]
        if o2_min is not None and (o2 is None or o2 < o2_min):
            continue
        if o2_max is not None and (o2 is None or o2 > o2_max):
            continue
        if p_min is not None and (p is None or p < p_min):
            continue
        if p_max is not None and (p is None or p > p_max):
            continue
        out.append(t)
    return out


@app.get("/api/tests")
def tests(investigation: Optional[str] = None, phase: Optional[str] = None, fuel: Optional[str] = None,
          o2_min: Optional[float] = None, o2_max: Optional[float] = None,
          p_min: Optional[float] = None, p_max: Optional[float] = None):
    return filter_tests(investigation, phase, o2_min, o2_max, p_min, p_max, fuel)


@app.get("/api/export/tests.csv")
def export_csv(investigation: Optional[str] = None, phase: Optional[str] = None, fuel: Optional[str] = None,
               o2_min: Optional[float] = None, o2_max: Optional[float] = None,
               p_min: Optional[float] = None, p_max: Optional[float] = None):
    rows = filter_tests(investigation, phase, o2_min, o2_max, p_min, p_max, fuel)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=TEST_COLS, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=firesight_tests.csv"})


@app.get("/api/analytics")
def analytics():
    return store()["analytics"]


@app.get("/api/compare")
def compare(ids: str):
    s = store()
    chosen = [s["investigations"][i] for i in ids.split(",") if i in s["investigations"]]
    pairs = [x for x in s["similarity"] if x["a"] in ids and x["b"] in ids]
    fields = ["fuel_phase", "platform_name", "fuels_canon", "o2_range", "p_range_kpa", "flow_range_cm_s",
              "sensor_categories", "variables", "constants", "pillars"]
    same, diff = [], []
    for f in fields:
        vals = [str(c.get(f)) for c in chosen]
        (same if len(set(vals)) == 1 else diff).append(f)
    return {"investigations": chosen, "pairs": pairs, "same_fields": same, "different_fields": diff}


class RankBody(BaseModel):
    scenario: str = "lunar_base"
    weights: Optional[dict] = None
    pillars: Optional[dict] = None


def _clean_weights(given, allowed, default):
    out = {}
    for k in allowed:
        v = (given or {}).get(k, default.get(k, 0) if given is None else 0)
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise HTTPException(400, f"Weight '{k}' must be a number")
        if not math.isfinite(v) or v < 0 or v > 100:
            raise HTTPException(400, f"Weight '{k}' must be between 0 and 100")
        out[k] = v
    return out


@app.post("/api/rank")
def rank(body: RankBody):
    a = store()["analytics"]
    scenarios = {k[4:] for f in a["ranking_features"].values() for k in f if k.startswith("atm_")}
    if body.scenario not in scenarios:
        raise HTTPException(400, f"Unknown scenario; use one of: {', '.join(sorted(scenarios))}")
    w = _clean_weights(body.weights, list(a["default_weights"]), a["default_weights"])
    pw = _clean_weights(body.pillars, ["prevention", "detection", "suppression"], {"prevention": 1, "detection": 1, "suppression": 1})
    tot_w = sum(w.values()) or 1
    tot_p = sum(pw.values()) or 1
    rows = []
    for acc, f in a["ranking_features"].items():
        parts = {"atmosphere": f[f"atm_{body.scenario}"],
                 "pillar": sum(f[f"pillar_{k}"] * v for k, v in pw.items()) / tot_p,
                 "realism": f["realism"], "data_depth": f["data_depth"], "scale": f["scale"], "flight": f["flight"]}
        rows.append({"id": acc, "score": round(100 * sum(w[k] * parts[k] for k in w) / tot_w, 1), "parts": parts})
    return sorted(rows, key=lambda r: -r["score"])


@app.get("/api/search")
def search_api(q: str = Query(..., min_length=2, max_length=300), k: int = Query(10, ge=1, le=50),
               investigation: Optional[str] = Query(None, max_length=20)):
    return search(q, k=k, investigation=investigation)


class Ask(BaseModel):
    question: str
    investigation: Optional[str] = None
    use_llm: bool = True


_LLM_CALLS = {"day": "", "n": 0, "ip": {}}
LLM_PER_IP_PER_MIN = int(os.environ.get("FIRESIGHT_LLM_PER_MIN", "6"))
LLM_PER_DAY = int(os.environ.get("FIRESIGHT_LLM_PER_DAY", "500"))


def _llm_allowed(ip: str) -> bool:
    """Protects the free AI quota: per-visitor and daily caps. Over the cap, answers fall back to cited extracts."""
    now = time.time(); day = time.strftime("%Y-%m-%d")
    if _LLM_CALLS["day"] != day:
        _LLM_CALLS.update(day=day, n=0, ip={})
    recent = [t for t in _LLM_CALLS["ip"].get(ip, []) if now - t < 60]
    if len(recent) >= LLM_PER_IP_PER_MIN or _LLM_CALLS["n"] >= LLM_PER_DAY:
        _LLM_CALLS["ip"][ip] = recent
        return False
    _LLM_CALLS["ip"][ip] = recent + [now]
    _LLM_CALLS["n"] += 1
    return True


@app.post("/api/ask")
def ask(body: Ask, request: Request):
    q = body.question.strip()
    if len(q) < 3:
        raise HTTPException(400, "Question too short")
    if len(q) > 600:
        raise HTTPException(400, "Question too long (600 characters maximum)")
    if body.investigation and len(body.investigation) > 20:
        raise HTTPException(400, "Invalid investigation id")
    ip = (request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "?"))
    use_llm = body.use_llm and _llm_allowed(ip)
    return answer(q, body.investigation, use_llm)


DIST = Path(os.environ.get("FIRESIGHT_STATIC", ROOT / "frontend" / "dist"))
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    for sub in ("data", "media"):
        if (DIST / sub).exists():
            app.mount(f"/{sub}", StaticFiles(directory=DIST / sub), name=sub)

    DIST_ROOT = DIST.resolve()

    @app.get("/{path:path}")
    def spa(path: str):
        # Serve only files that resolve inside the built dashboard folder (blocks ../ and encoded traversal).
        if path:
            try:
                f = (DIST_ROOT / path).resolve()
            except (OSError, ValueError):
                f = None
            if f is not None and DIST_ROOT in f.parents and f.is_file():
                return FileResponse(f)
        return FileResponse(DIST_ROOT / "index.html")
