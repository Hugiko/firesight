"""Question answering grounded in NASA sources.

Mode 1 (LLM): an open model writes the answer from the retrieved passages and must cite them as [n].
  - Hosted: if FIRESIGHT_LLM_API_KEY is set, any OpenAI-compatible endpoint is used
    (default: Groq's free tier, Llama 3.1 8B; base URL FIRESIGHT_LLM_API_URL, model FIRESIGHT_LLM_API_MODEL).
  - Local: otherwise, an Ollama server if reachable (FIRESIGHT_LLM_URL), e.g. Qwen 2.5.
Mode 2 (extractive, always available): the best-matching sentences are returned verbatim with citations,
plus measured tests near any oxygen / pressure mentioned in the question.
"""
import json
import os
import re
import urllib.request
from collections import Counter

from .search import nearest_tests, parse_conditions, search

LLM_URL = os.environ.get("FIRESIGHT_LLM_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.environ.get("FIRESIGHT_LLM_MODEL", "qwen2.5:3b")
LLM_TIMEOUT = float(os.environ.get("FIRESIGHT_LLM_TIMEOUT", "90"))
API_KEY = os.environ.get("FIRESIGHT_LLM_API_KEY", "").strip()
API_URL = os.environ.get("FIRESIGHT_LLM_API_URL", "https://api.groq.com/openai/v1").rstrip("/")
API_MODEL = os.environ.get("FIRESIGHT_LLM_API_MODEL", "llama-3.1-8b-instant")

SYSTEM = (
    "You are FireSight, a NASA fire-safety research assistant for aerospace engineers and students. "
    "Answer ONLY from the numbered sources and measured-test table provided. Cite every factual sentence with [n]. "
    "If the sources do not contain the answer, say so plainly and suggest which investigation would be relevant. "
    "Never invent numbers. Be concise: 3-6 sentences, then one line starting 'Data gap:' if relevant."
)


def llm_backend():
    """'api', 'local' or None."""
    if os.environ.get("FIRESIGHT_LLM", "on") == "off":
        return None
    if API_KEY:
        return "api" if _api_ready() else None
    return "local" if _ollama_ready() else None


_API_CHECK = {"t": 0.0, "ok": False}


def _api_ready():
    """Validates the key against /models at most every 10 minutes (no tokens are spent)."""
    import time
    if time.time() - _API_CHECK["t"] < 600:
        return _API_CHECK["ok"]
    try:
        req = urllib.request.Request(API_URL + "/models", headers={"Authorization": f"Bearer {API_KEY}", "User-Agent": "FireSight/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            _API_CHECK["ok"] = r.status == 200
    except Exception:
        _API_CHECK["ok"] = False
    _API_CHECK["t"] = time.time()
    return _API_CHECK["ok"]


def llm_available():
    return llm_backend() is not None


_LOCAL_CHECK = {"t": 0.0, "ok": False}


def _ollama_ready():
    """Is a local Ollama model reachable? Cached for 5 minutes so requests never wait on a missing server."""
    import time
    if os.environ.get("FIRESIGHT_LLM_LOCAL", "on") == "off":
        return False
    if time.time() - _LOCAL_CHECK["t"] < 300:
        return _LOCAL_CHECK["ok"]
    _LOCAL_CHECK["ok"] = _ollama_probe()
    _LOCAL_CHECK["t"] = time.time()
    return _LOCAL_CHECK["ok"]


def _ollama_probe():
    try:
        with urllib.request.urlopen(LLM_URL + "/api/tags", timeout=1) as r:
            tags = json.loads(r.read())
        return any(m.get("name", "").startswith(LLM_MODEL.split(":")[0]) for m in tags.get("models", []))
    except Exception:
        return False


def _context(passages, tests):
    blocks = [f"[{i}] ({p['source']}: {p['title']}{', p.' + str(p['page']) if p['page'] else ''}) {p['text']}"
              for i, p in enumerate(passages, 1)]
    if tests:
        rows = "\n".join(f"- {t['test_id']} ({t['investigation']}): {t['fuel']}, O2 {t['o2_pct']}%, "
                         f"P {t['pressure_kpa']} kPa -> {t['outcome']}, burn {t['burn_time_s']} s" for t in tests)
        blocks.append(f"[T] Measured microgravity tests nearest to the question's conditions:\n{rows}")
    return "\n\n".join(blocks)


def _ask_api(question, passages, tests):
    body = {"model": API_MODEL, "temperature": 0.1, "max_tokens": 400,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": f"Sources:\n{_context(passages, tests)}\n\nQuestion: {question}"}]}
    req = urllib.request.Request(API_URL + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}",
                                          "User-Agent": "FireSight/1.0"})
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def _ask_llm(question, passages, tests):
    if llm_backend() == "api":
        return _ask_api(question, passages, tests)
    body = {"model": LLM_MODEL, "stream": False, "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 280},
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": f"Sources:\n{_context(passages, tests)}\n\nQuestion: {question}"}]}
    req = urllib.request.Request(LLM_URL + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as r:
        return json.loads(r.read())["message"]["content"].strip()


def _sentences(text):
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)]
    return [s for s in parts if 40 <= len(s) <= 400 and s[0].isupper()]


def _extractive(question, passages):
    qwords = {w for w in re.findall(r"[a-z0-9]+", question.lower()) if len(w) > 3}
    cand = []
    for i, p in enumerate(passages, 1):
        for s in _sentences(p["text"]):
            words = set(re.findall(r"[a-z0-9]+", s.lower()))
            overlap = len(qwords & words)
            if overlap:
                cand.append((overlap + p["score"] * 5, i, s))
    cand.sort(key=lambda x: -x[0])
    picked, used = [], set()
    for _, i, s in cand:
        if s in used:
            continue
        used.add(s)
        picked.append(f"{s} [{i}]")
        if len(picked) == 4:
            break
    return " ".join(picked)


LAST_LLM_ERROR = {"error": None}


def _describe_error(e):
    msg = f"{type(e).__name__}"
    code = getattr(e, "code", None)
    if code:
        msg += f" {code}"
    try:
        body = e.read().decode("utf-8", "replace")[:300] if hasattr(e, "read") else str(e)[:300]
    except Exception:
        body = str(e)[:300]
    if API_KEY:
        body = body.replace(API_KEY, "***")
    return f"{msg}: {body}"


def summarize_tests(tests):
    if not tests:
        return None
    c = Counter(t["outcome"] for t in tests)
    invs = Counter(t["investigation"] for t in tests)
    return {"n": len(tests), "outcomes": dict(c), "investigations": dict(invs)}


HISTORY_WORDS = re.compile(r"apollo|mir\b|artemis|accident|history|incident|spinoff|firefight", re.I)
SOLID_WORDS = re.compile(r"fabric|textile|cloth|plastic|pmma|material|solid|nomex|cotton|foam", re.I)


def data_summary(question, cond, tests):
    """Plain-language summary of measured tests near the requested atmosphere."""
    if not tests:
        return None
    by_inv = Counter(t["investigation"] for t in tests)
    by_out = Counter(t["outcome"] or "not recorded" for t in tests)
    inv_txt = ", ".join(f"{n} from {i}" for i, n in by_inv.most_common())
    out_txt = ", ".join(f"{n} {o}" for o, n in by_out.most_common())
    phases = Counter(t["fuel_phase"] for t in tests)
    s = (f"FireSight found {len(tests)} measured microgravity tests near {cond['o2_pct']}% O2"
         f"{' and ' + str(cond['pressure_kpa']) + ' kPa' if cond.get('pressure_kpa') else ''} ({inv_txt}); outcomes: {out_txt} [T].")
    if SOLID_WORDS.search(question) and "solid" not in phases:
        s += (" None of them are solid materials: fabric and plastic flammability at this atmosphere is an open data gap in PSI"
              " (all tabulated BASS and Saffire tests are at cabin air).")
    return s


def answer(question, investigation=None, use_llm=True):
    passages = search(question, k=6, investigation=investigation)
    if not HISTORY_WORDS.search(question):
        passages = [p for p in passages if p["kind"] != "history"] or passages
    cond = parse_conditions(question)
    tests = nearest_tests(cond)
    mode, text = "extractive", None
    backend = llm_backend() if use_llm else None
    if backend:
        try:
            text = _ask_llm(question, passages, tests)
            mode = "llm"
            LAST_LLM_ERROR["error"] = None
        except Exception as e:  # keep serving cited extracts, but record why (never the key)
            LAST_LLM_ERROR["error"] = _describe_error(e)
            print("FireSight LLM error:", LAST_LLM_ERROR["error"], flush=True)
            text = None
    if not text:
        ext = _extractive(question, passages) or "No passage in the NASA sources matches this question closely."
        ds = data_summary(question, cond, tests)
        text = f"{ds} {ext}" if ds else ext
    return {"question": question, "answer": text, "mode": mode, "model": (API_MODEL if backend == "api" else LLM_MODEL) if mode == "llm" else None, "conditions": cond,
            "sources": [{"n": i, "source": p["source"], "title": p["title"], "url": p["url"], "page": p["page"],
                         "investigation": p["investigation"], "excerpt": p["text"][:500]} for i, p in enumerate(passages, 1)],
            "tests": tests}
