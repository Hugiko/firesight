"""Model Lab: retrain the FLEX flame-persistence model on the server, in real time.

Same recipe as the offline pipeline (pipeline/intelligence.py): logistic regression (L2, C = 1) on
[O2 %, ln(pressure kPa), CO2 %, He %, heptane], standardized, validated with 5-fold stratified cross-validation
(scaler fitted inside each fold), and bootstrap refits for 90 % intervals.

Uploaded rows are used only for the request that sent them: they are never stored, and the official model
shipped with the dashboard is never changed.
"""
import json
import math
import threading
import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import store

FEATURES = ["O₂ %", "ln(P)", "CO₂ %", "He %", "heptane"]
FUELS = {"heptane": 1, "n-heptane": 1, "methanol": 0}
TRUE = {"1", "true", "yes", "y", "persists", "burns", "burned", "burning"}
FALSE = {"0", "false", "no", "n", "extinction", "extinguished", "out", "goes out", "flame extinction"}
MAX_ROWS = 5000
LOCK = threading.Lock()


def nasa_rows():
    rows = []
    for t in store()["tests"]:
        if t["investigation"] != "PSI-69" or not t["pressure_kpa"] or not t["o2_pct"]:
            continue
        rows.append({"test_id": t["test_id"], "o2_pct": t["o2_pct"], "pressure_kpa": t["pressure_kpa"],
                     "co2_pct": t["co2_pct"] or 0, "he_pct": t["he_pct"] or 0, "fuel": t["fuel"],
                     "flame_persists": 0 if t["outcome"] == "flame extinction" else 1, "source": "NASA FLEX"})
    return rows


def template_csv() -> str:
    cols = ["test_id", "o2_pct", "pressure_kpa", "co2_pct", "he_pct", "fuel", "flame_persists", "source"]
    lines = [",".join(cols)] + [",".join(str(r[c]) for c in cols) for r in nasa_rows()]
    return "\n".join(lines) + "\n"


def _num(v, name, lo, hi, default=None):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        if default is not None:
            return default
        raise ValueError(f"{name} is missing")
    try:
        x = float(str(v).replace(",", ".")) if isinstance(v, str) else float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{name} is not a number")
    if not math.isfinite(x) or x < lo or x > hi:
        raise ValueError(f"{name} must be between {lo} and {hi}")
    return x


def clean_user_rows(raw):
    """Validates uploaded rows. Returns (accepted, rejected[(row number, reason)])."""
    ok, bad = [], []
    for i, r in enumerate(raw[:MAX_ROWS], start=1):
        try:
            if not isinstance(r, dict):
                raise ValueError("row is not an object")
            o2 = _num(r.get("o2_pct"), "o2_pct", 1, 100)
            p = _num(r.get("pressure_kpa"), "pressure_kpa", 1, 1000)
            co2 = _num(r.get("co2_pct"), "co2_pct", 0, 100, 0.0)
            he = _num(r.get("he_pct"), "he_pct", 0, 100, 0.0)
            if o2 + co2 + he > 100.5:
                raise ValueError("o2 + co2 + he exceeds 100 %")
            fuel = str(r.get("fuel", "")).strip().lower()
            if fuel not in FUELS:
                raise ValueError("fuel must be heptane or methanol (the FLEX model's fuels)")
            lab = str(r.get("flame_persists", "")).strip().lower()
            if lab in TRUE:
                y = 1
            elif lab in FALSE:
                y = 0
            else:
                raise ValueError("flame_persists must be 1 (keeps burning) or 0 (goes out)")
            ok.append({"test_id": str(r.get("test_id") or f"USER-{i:03d}")[:40], "o2_pct": o2, "pressure_kpa": p, "co2_pct": co2,
                       "he_pct": he, "fuel": "Heptane" if FUELS[fuel] else "Methanol", "flame_persists": y, "source": "user-supplied"})
        except ValueError as e:
            bad.append((i, str(e)))
    if len(raw) > MAX_ROWS:
        bad.append((MAX_ROWS + 1, f"only the first {MAX_ROWS} rows are used"))
    return ok, bad


def _xy(rows):
    X = np.array([[r["o2_pct"], math.log(r["pressure_kpa"]), r["co2_pct"], r["he_pct"], 1 if r["fuel"] == "Heptane" else 0] for r in rows], float)
    y = np.array([r["flame_persists"] for r in rows], int)
    return X, y


def _model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))


def run(body, user_rows, rejected):
    """Generator of progress events (dicts). The last event has type 'result' or 'error'."""
    t0 = time.perf_counter()
    el = lambda: round(time.perf_counter() - t0, 3)
    ev = lambda kind, text, progress, **kw: {"type": kind, "text": text, "t": el(), "progress": round(progress, 3), **kw}

    base = nasa_rows() if body.dataset in ("nasa", "nasa+user") else []
    rng = np.random.default_rng(body.seed)
    if base and body.nasa_fraction < 1:
        keep = rng.permutation(len(base))[: max(10, int(round(len(base) * body.nasa_fraction)))]
        base = [base[i] for i in sorted(keep)]
    rows = base + (user_rows if body.dataset in ("nasa+user", "user") else [])
    yield ev("start", f"Dataset: {len(base)} NASA FLEX tests + {len(rows) - len(base)} user tests"
             + (f" ({len(rejected)} uploaded rows rejected)" if rejected else ""), 0.02)

    X, y = _xy(rows) if rows else (np.zeros((0, 5)), np.zeros(0, int))
    n1 = int(y.sum())
    if len(y) < 20 or n1 < 5 or len(y) - n1 < 5:
        yield ev("error", f"Not enough data to train: need at least 20 tests with 5 of each outcome (got {len(y)}: {n1} persist, {len(y) - n1} go out).", 1)
        return
    if body.shuffle:
        y = rng.permutation(y)
        yield ev("done", "Permutation test: outcome labels shuffled at random (the link between conditions and outcome is destroyed)", 0.05)
    yield ev("done", f"Features built: X = [O₂, ln P, CO₂, He, heptane] · {len(y)} × 5 matrix · {n1} persist / {len(y) - n1} go out", 0.08)

    # 5-fold stratified cross-validation, fold by fold so progress is real
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=7)
    pred = np.zeros(len(y)); pred_o2 = np.zeros(len(y))
    for k, (tr, te) in enumerate(cv.split(X, y), start=1):
        m = _model().fit(X[tr], y[tr]); pred[te] = m.predict_proba(X[te])[:, 1]
        m1 = _model().fit(X[tr][:, :1], y[tr]); pred_o2[te] = m1.predict_proba(X[te][:, :1])[:, 1]
        fold_auc = roc_auc_score(y[te], pred[te]) if len(set(y[te])) == 2 else float("nan")
        yield ev("done", f"Fold {k}/5: trained on {len(tr)} tests, predicted {len(te)} unseen tests · fold AUC {fold_auc:.3f}", 0.08 + 0.22 * k / 5)
    auc = float(roc_auc_score(y, pred)); auc_o2 = float(roc_auc_score(y, pred_o2))
    brier = float(brier_score_loss(y, pred)); base_rate = float(y.mean())
    brier_base = float(brier_score_loss(y, np.full(len(y), base_rate)))
    acc = float(((pred >= 0.5) == y).mean())
    yield ev("result", f"Cross-validated AUC {auc:.3f} (O₂ only {auc_o2:.3f}) · Brier {brier:.3f} (no-skill {brier_base:.3f})", 0.32)

    # Final fit on all rows
    full = _model().fit(X, y)
    sc, lr = full.named_steps["standardscaler"], full.named_steps["logisticregression"]
    coef_std = [round(float(c), 3) for c in lr.coef_[0]]
    yield ev("done", "Final model fitted on all tests: " + " · ".join(f"{f} {c:+.2f}" for f, c in zip(FEATURES, coef_std)), 0.36)

    # Bootstrap refits for the uncertainty band
    mu, sd = sc.mean_, np.where(sc.scale_ == 0, 1, sc.scale_)
    Xs = (X - mu) / sd
    boots = []
    B = body.n_boot
    step = max(1, B // 10)
    for b in range(B):
        idx = rng.integers(0, len(y), len(y))
        if len(set(y[idx])) < 2:
            continue
        m = LogisticRegression(C=1.0, max_iter=2000).fit(Xs[idx], y[idx])
        boots.append([float(m.intercept_[0])] + [float(c) for c in m.coef_[0]])
        if (b + 1) % step == 0 or b + 1 == B:
            yield ev("progress", f"Bootstrap refit {b + 1}/{B}", 0.36 + 0.56 * (b + 1) / B)
    boots = np.array(boots)
    orr = np.exp(boots[:, 1] / sd[0])
    yield ev("done", f"{len(boots)} bootstrap models trained · odds ratio per +1 pt O₂ ×{np.median(orr):.2f} (90% CI {np.percentile(orr, 5):.2f}–{np.percentile(orr, 95):.2f})", 0.94)

    curves = []
    o2s = np.arange(10, 41, 1.0)
    for fuel, hept in (("Heptane", 1), ("Methanol", 0)):
        for p in (101.3, 70.3):
            Z = (np.column_stack([o2s, np.full_like(o2s, math.log(p)), 0 * o2s, 0 * o2s, np.full_like(o2s, hept)]) - mu) / sd
            pr = 1 / (1 + np.exp(-(boots[:, :1] + boots[:, 1:] @ Z.T)))
            q = np.percentile(pr, [5, 50, 95], axis=0)
            curves.append({"fuel": fuel, "p_kpa": p, "points": [[float(o), round(float(q[0, i]), 4), round(float(q[1, i]), 4), round(float(q[2, i]), 4)] for i, o in enumerate(o2s)]})
    lunar = float(np.median(1 / (1 + np.exp(-(boots[:, 0] + boots[:, 1:] @ ((np.array([34, math.log(56.5), 0, 0, 1]) - mu) / sd))))))
    calib = []
    for lo in np.arange(0, 1, 0.2):
        sel = (pred >= lo) & (pred < lo + 0.2 + (1e-9 if lo >= 0.8 else 0))
        if sel.sum():
            calib.append({"lo": round(float(lo), 1), "hi": round(float(lo + 0.2), 1), "n": int(sel.sum()), "pred": round(float(pred[sel].mean()), 3), "obs": round(float(y[sel].mean()), 3)})

    yield ev("final", f"Model trained in {el():.2f} s · Moon-base atmosphere (34% O₂, 56.5 kPa, heptane): {lunar * 100:.0f}% persistence", 1.0, result={
        "n": int(len(y)), "n_nasa": len(base), "n_user": len(rows) - len(base), "n_persist": n1, "rejected": [{"row": r, "reason": m} for r, m in rejected[:20]],
        "n_rejected": len(rejected), "shuffled": bool(body.shuffle), "nasa_fraction": body.nasa_fraction,
        "auc": round(auc, 3), "auc_o2_only": round(auc_o2, 3), "brier": round(brier, 3), "brier_baseline": round(brier_base, 3),
        "accuracy": round(acc, 3), "base_rate": round(base_rate, 3), "coefficients_standardized": dict(zip(FEATURES, coef_std)),
        "odds_ratio_per_o2_point": {"median": round(float(np.median(orr)), 3), "p05": round(float(np.percentile(orr, 5)), 3), "p95": round(float(np.percentile(orr, 95)), 3)},
        "n_bootstrap": int(len(boots)), "curves": curves, "lunar_persist": round(lunar, 4), "calibration": calib, "seconds": el()})


def stream(body, user_rows, rejected):
    if not LOCK.acquire(timeout=20):
        yield json.dumps({"type": "error", "text": "The server is training another model right now. Try again in a few seconds.", "t": 0, "progress": 1}) + "\n"
        return
    try:
        for e in run(body, user_rows, rejected):
            yield json.dumps(e, ensure_ascii=False) + "\n"
    except Exception as e:  # report instead of breaking the stream
        yield json.dumps({"type": "error", "text": f"Training failed: {type(e).__name__}", "t": 0, "progress": 1}) + "\n"
    finally:
        LOCK.release()
