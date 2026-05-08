"""
FastAPI backend for Init-Diagnose clinical triage pipeline.

Run: uvicorn app.api:app --reload --port 8080
"""
import sys
import re
import time
from pathlib import Path
import asyncio
import queue
import threading
import json
from fastapi.responses import StreamingResponse

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from risk_scorer.scorer import RiskScorer

app = FastAPI(title="Init-Diagnose", version="1.0")
scorer = RiskScorer()

# Preload GraphRAG pipeline so MPS model loads on main thread
_graphrag_pipeline = None

@app.on_event("startup")
async def startup():
    global _graphrag_pipeline
    import torch
    if torch.backends.mps.is_available():
        _ = torch.zeros(1).to("mps")  # init MPS on main thread
    print("Preloading GraphRAG pipeline...")
    try:
        from graphrag.pipeline import GraphRAGPipeline
        _graphrag_pipeline = await asyncio.to_thread(GraphRAGPipeline)
        print("GraphRAG pipeline ready.")
    except Exception as e:
        print(f"GraphRAG preload failed: {e}")

# ── Note quality analyzer ──────────────────────────────────────────────────────

_PHQ9_RE  = re.compile(r"phq[-\s]?9[^\d]{0,10}(\d+)", re.I)
_GAF_RE   = re.compile(r"gaf[^\d]{0,10}(\d+)", re.I)

_DIAGNOSES = [
    "bipolar", "schizophrenia", "schizoaffective", "major depressive",
    "generalized anxiety", "ptsd", "borderline personality", "ocd",
    "panic disorder", "adhd", "autism",
]
_MEDS = [
    "quetiapine", "risperidone", "aripiprazole", "olanzapine", "lithium",
    "valproate", "lamotrigine", "sertraline", "fluoxetine", "escitalopram",
    "venlafaxine", "clonazepam", "lorazepam",
]
_SUICIDAL = ["suicid", "self-harm", "kill himself", "kill herself", "end his life"]
_SEVERITY = ["severe", "acute", "critical"]


def _score_note(note: str) -> tuple[int, dict]:
    n = note.lower()
    breakdown = {
        "phq9_present":      bool(_PHQ9_RE.search(n)),
        "gaf_present":       bool(_GAF_RE.search(n)),
        "named_diagnosis":   any(d in n for d in _DIAGNOSES),
        "named_medication":  any(m in n for m in _MEDS),
        "suicidal_explicit": any(s in n for s in _SUICIDAL),
        "severity_explicit": any(s in n for s in _SEVERITY),
    }
    score = sum(breakdown.values())
    return score, breakdown


def _select_mode(note: str) -> tuple[str, int, dict, str]:
    score, breakdown = _score_note(note)
    if score >= 3:
        mode   = "fast"
        reason = f"Note has {score}/6 structured signals — fast mode sufficient."
    else:
        mode   = "full"
        reason = f"Note has only {score}/6 structured signals — using graph for context."
    return mode, score, breakdown, reason

_KNOWN_DX = [
    "Major Depressive Disorder", "Bipolar I Disorder", "Bipolar II Disorder",
    "Schizophrenia", "Schizoaffective Disorder", "PTSD",
    "Generalized Anxiety Disorder", "Panic Disorder", "OCD",
    "Borderline Personality Disorder", "ADHD",
]
_KNOWN_MEDS = [
    "Sertraline", "Fluoxetine", "Escitalopram", "Venlafaxine", "Duloxetine",
    "Bupropion", "Lithium", "Valproate", "Lamotrigine", "Quetiapine",
    "Risperidone", "Aripiprazole", "Olanzapine", "Clonazepam", "Lorazepam",
]
_KNOWN_SYMS = [
    "suicidal ideation", "hallucinations", "delusions", "paranoia",
    "anhedonia", "insomnia", "fatigue", "panic attacks", "flashbacks",
    "racing thoughts", "dissociation", "grandiosity",
]

def _build_graph(note: str, context: str) -> dict:
    combined = (note + " " + context).lower()
    nodes = [{"id": "patient", "name": "Patient", "type": "patient", "val": 25}]
    links = []
    seen = set()

    m = re.search(r"phq[-\s]?9[^\d]{0,10}(\d+)", combined)
    if m:
        nodes.append({"id": "phq9", "name": f"PHQ-9: {m.group(1)}", "type": "assessment", "val": 10})
        links.append({"source": "patient", "target": "phq9", "label": "HAS_ASSESSMENT"})

    m = re.search(r"gaf[^\d]{0,10}(\d+)", combined)
    if m:
        nodes.append({"id": "gaf", "name": f"GAF: {m.group(1)}", "type": "assessment", "val": 10})
        links.append({"source": "patient", "target": "gaf", "label": "HAS_ASSESSMENT"})

    for dx in _KNOWN_DX:
        if dx.lower() in combined:
            nid = f"dx_{dx[:10]}"
            if nid not in seen:
                nodes.append({"id": nid, "name": dx, "type": "diagnosis", "val": 14})
                links.append({"source": "patient", "target": nid, "label": "HAS_DIAGNOSIS"})
                seen.add(nid)

    for med in _KNOWN_MEDS:
        if med.lower() in combined:
            nid = f"med_{med}"
            if nid not in seen:
                nodes.append({"id": nid, "name": med, "type": "medication", "val": 10})
                links.append({"source": "patient", "target": nid, "label": "PRESCRIBED"})
                seen.add(nid)

    for sym in _KNOWN_SYMS:
        if sym in combined:
            nid = f"sym_{sym[:10]}"
            if nid not in seen:
                nodes.append({"id": nid, "name": sym.title(), "type": "symptom", "val": 8})
                links.append({"source": "patient", "target": nid, "label": "PRESENTS"})
                seen.add(nid)

    return {"nodes": nodes, "links": links}

# ── Request / Response schemas ─────────────────────────────────────────────────

class InferRequest(BaseModel):
    note: str
    mode_override: str | None = None   # "fast" | "full" | None (auto)


class InferResponse(BaseModel):
    risk_score:     float
    triage_level:   str
    recommendation: str
    top_factors:    list[dict]
    mode_used:      str
    mode_reason:    str
    latency_ms:     float
    graphrag_context: str | None = None
    graph_data: dict | None = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    auto_mode, score, breakdown, reason = _select_mode(req.note)
    mode = req.mode_override if req.mode_override in ("fast", "full") else auto_mode

    if req.mode_override:
        reason = f"Manual override → {mode} mode. (Auto would choose: {auto_mode})"

    t0 = time.perf_counter()
    graphrag_context = None

    if mode == "full":
        pipeline = _graphrag_pipeline
        if pipeline is None:
            raise RuntimeError("GraphRAG pipeline not available")
        graphrag_result = pipeline.run(req.note, progress_callback=lambda e: q.put(e))
    else:
        graphrag_result = {
            "full_context": "",
            "total_queries": 0,
            "successful_queries": 0,
        }

    result = scorer.score(req.note, graphrag_result)
    latency_ms = (time.perf_counter() - t0) * 1000
    graph_data = _build_graph(req.note, graphrag_result.get("full_context", ""))
    return InferResponse(
        risk_score=result["risk_score"],
        triage_level=result["triage_level"],
        recommendation=result["recommendation"],
        top_factors=result["top_factors"],
        mode_used=mode,
        mode_reason=reason,
        latency_ms=round(latency_ms, 2),
        graphrag_context=graphrag_context,
        graph_data=graph_data,
    )
    
@app.post("/infer/stream")
async def infer_stream(req: InferRequest):
    q: queue.Queue = queue.Queue()

    def run():
        try:
            auto_mode, score, _, reason = _select_mode(req.note)
            mode = req.mode_override if req.mode_override in ("fast", "full") else auto_mode
            q.put({"type": "progress", "step": "info", "msg": f"Note quality: {score}/6 — {mode} mode selected"})

            if mode == "full":
                pipeline = _graphrag_pipeline
                if pipeline is None:
                    raise RuntimeError("GraphRAG pipeline not available")
                graphrag_result = pipeline.run(req.note, progress_callback=lambda e: q.put(e))
            else:
                q.put({"type": "progress", "step": "info", "msg": "Extracting features from note..."})
                graphrag_result = {"full_context": "", "total_queries": 0, "successful_queries": 0}

            q.put({"type": "progress", "step": "info", "msg": "Scoring risk with XGBoost..."})
            result = scorer.score(req.note, graphrag_result)
            graph_data = _build_graph(req.note, graphrag_result.get("full_context", ""))

            q.put({"type": "done", "result": {
                "risk_score":       result["risk_score"],
                "triage_level":     result["triage_level"],
                "recommendation":   result["recommendation"],
                "top_factors":      result["top_factors"],
                "mode_used":        mode,
                "mode_reason":      reason,
                "latency_ms":       0,
                "graphrag_context": graphrag_result.get("full_context"),
                "graph_data":       graph_data,
            }})
        except Exception as e:
            q.put({"type": "error", "msg": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=run, daemon=True).start()

    async def generate():
        loop = asyncio.get_event_loop()
        while True:
            event = await loop.run_in_executor(None, lambda: q.get(timeout=300))
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# ── Static files (UI) ──────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return FileResponse("app/static/index.html")