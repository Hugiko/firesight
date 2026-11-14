"""Semantic-ish retrieval over NASA texts (TF-IDF with word n-grams and sublinear tf) plus
structured lookup of measured tests when the question mentions oxygen / pressure values."""
import math
import re
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .data import store

SYNONYMS = {
    "moon": "moon lunar habitat base", "lunar": "lunar moon habitat", "mars": "mars martian habitat",
    "extinguish": "extinguish extinction suppression suppressant", "suppression": "suppression suppressant extinguish",
    "smoke": "smoke aerosol particle detector", "detector": "detector detection smoke alarm",
    "fabric": "fabric sibal cotton textile nomex", "plastic": "plastic pmma polymer acrylic",
    "flammability": "flammability flammable limit oxygen index", "oxygen": "oxygen o2",
    "droplet": "droplet liquid fuel", "soot": "soot smoke point radiation",
}

KIND_WEIGHT = {"finding": 1.25, "psi": 1.15, "factsheet": 1.1, "guide": 1.0, "ntrs": 1.0, "ntrs_page": 0.9, "history": 1.0}


def expand(q):
    words = re.findall(r"[a-z0-9]+", q.lower())
    return q + " " + " ".join(SYNONYMS[w] for w in words if w in SYNONYMS)


@lru_cache(maxsize=1)
def index():
    chunks = store()["chunks"]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True, min_df=1, max_df=0.6)
    mat = vec.fit_transform([f"{c['title']} {c['text']}" for c in chunks])
    return vec, mat, chunks


def search(q, k=8, investigation=None):
    vec, mat, chunks = index()
    qv = vec.transform([expand(q)])
    scores = (mat @ qv.T).toarray().ravel()
    for i, c in enumerate(chunks):
        scores[i] *= KIND_WEIGHT.get(c["kind"], 1.0)
        if investigation and c["investigation"] == investigation:
            scores[i] *= 1.5
    order = np.argsort(-scores)
    out, seen = [], set()
    for i in order:
        if scores[i] <= 0 or len(out) >= k:
            break
        c = chunks[i]
        key = (c["title"], c["page"])
        if key in seen:
            continue
        seen.add(key)
        out.append({**c, "score": round(float(scores[i]), 4)})
    return out


UNIT_P = [(r"(\d+(?:\.\d+)?)\s*psi", 6.894757), (r"(\d+(?:\.\d+)?)\s*kpa", 1.0),
          (r"(\d+(?:\.\d+)?)\s*bar", 100.0), (r"(\d+(?:\.\d+)?)\s*atm", 101.325)]


def parse_conditions(q):
    ql = q.lower()
    cond = {}
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:o2|oxygen)?", ql)
    if m:
        cond["o2_pct"] = float(m.group(1))
    for pat, f in UNIT_P:
        m = re.search(pat, ql)
        if m:
            cond["pressure_kpa"] = round(float(m.group(1)) * f, 1)
            break
    for word, (o2, p) in {"lunar": (30, 70.3), "moon": (30, 70.3), "rover": (34, 56.5), "mars": (30, 70.3),
                          "spacesuit": (100, 29.6), "suit": (100, 29.6), "iss": (21, 101.3)}.items():
        if re.search(rf"\b{word}\b", ql):
            cond.setdefault("o2_pct", o2)
            cond.setdefault("pressure_kpa", p)
            cond.setdefault("scenario_word", word)
    return cond


def nearest_tests(cond, k=24, per_investigation=8):
    if "o2_pct" not in cond:
        return []
    p = cond.get("pressure_kpa")
    rows = []
    for t in store()["tests"]:
        if t["o2_pct"] is None:
            continue
        d = ((t["o2_pct"] - cond["o2_pct"]) / 5) ** 2
        if p and t["pressure_kpa"]:
            d += (math.log(t["pressure_kpa"] / p) / 0.25) ** 2
        elif p:
            continue
        rows.append((math.sqrt(d), t))
    rows.sort(key=lambda x: x[0])
    out, per = [], {}
    for d, t in rows:
        if d > 2.5 or len(out) >= k:
            break
        if per.get(t["investigation"], 0) >= per_investigation:
            continue
        per[t["investigation"]] = per.get(t["investigation"], 0) + 1
        out.append({**t, "distance": round(d, 2)})
    return out
