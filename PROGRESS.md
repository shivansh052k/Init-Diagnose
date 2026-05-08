# Init-Diagnose — Session Progress Log

## Project Overview
Ontology-Safe NL2Graph + GraphRAG Triage Framework
**Stack:** Neo4j · QLoRA (Qwen2.5-3B) · GraphRAG · XGBoost · SageMaker · Triton

---

## Architecture
```
Clinical Note (NL)
    ↓
Auto Mode Detection (note quality 0–6)
    ↓
[Fast path] Text-only features   |   [Full path] QLoRA Qwen2.5-3B → Cypher
                                 |       ↓
                                 |   Neo4j 110K-node psychiatry KG
                                 |       ↓
                                 |   GraphRAG context assembly
    ↓ ←──────────────────────────┘
Feature Extraction (16-dim, negation-aware NLP)
    ↓
XGBoost + Platt calibration (blended 10/90 with linear score)
    ↓
Triage output (score 0–100, level, factors, recommendation)
    ↓
┌──────────────────┬──────────────────────────────┐
│  Demo UI         │  Production Serving           │
│  FastAPI + SSE   │  Triton (batch=64, Prometheus)│
│  React + TS      │  AWS SageMaker endpoint       │
│  Glowing orb KG  │  P50/P95/P99 benchmark        │
└──────────────────┴──────────────────────────────┘
```

---

## Component Status

### ✅ Component 1: KG Builder (DONE)
- **Ontology:** 7 node types, 9 relationship types (DSM-5 aligned)
- **Nodes:** 110,573 total (Patient=30K, Assessment=50K, Episode=30K, Clinician=500, Diagnosis=23, Symptom=30, Medication=20)
- **Relationships:** 440,682 total
- **Neo4j:** Running on Docker (`localhost:7474`), bolt `localhost:7687`
- **Creds:** in `.env` (NEO4J_USER=neo4j, NEO4J_PASSWORD=initdiagnose123)
- **Key files:** `kg/schema/`, `kg/generators/`, `kg/loaders/`, `data/generate.py`

### ✅ Component 2: QLoRA Fine-tune Pipeline (DONE)
- **Model:** Qwen2.5-3B-Instruct, QLoRA fine-tuned on Colab T4
- **Training:** 200 steps, eval_loss=0.000147 (near-perfect)
- **Adapters:** saved at `nl2graph/train/adapters/`
- **Base model:** downloaded at `models/llama-3.2-3b-4bit/` (mlx format, NOT used for inference)
- **Inference:** uses `transformers` + `peft` on MPS (M3 Mac)
- **Eval:** 85% functional correctness on 20-query gold set (target: 92%)
- **Known issues:** Q7 (symptom vs assessment confusion), Q16 (insurance+category), Q18 (ASSESSED_BY vs TREATS)
- **Key files:** `nl2graph/data/`, `nl2graph/train/train_qlora.py`, `nl2graph/inference/nl2cypher.py`, `nl2graph/inference/schema_validator.py`

### ✅ Component 3: GraphRAG Retrieval (DONE)
- **Pipeline:** Clinical note → keyword extraction → NL questions → Cypher → Neo4j → context
- **Results:** 6 queries/note, ~3 successful avg, Neo4j exec 1-30ms
- **Total latency:** ~170s on M3 (expected — LLM inference bottleneck, not Neo4j)
- **On GPU/Triton:** target sub-150ms retrieval is achievable
- **Key files:** `graphrag/cypher_executor.py`, `graphrag/context_assembler.py`, `graphrag/retriever.py`, `graphrag/pipeline.py`

### ✅ Component 4: XGBoost Risk Scorer (DONE)
- **Model:** XGBoost + Platt calibration, trained on 5000 synthetic patients
- **Data:** 23.6% high-risk class balance, saved at `data/risk_train.npz`
- **AUROC:** 1.0 on synthetic data (expected — labels derived from features); real-world target ≥ 0.86
- **Top features:** has_bipolar_disorder, suicidal_ideation_severity, has_severe_episode, has_psychotic_disorder, phq9_norm
- **Model artifact:** `risk_scorer/model/xgb_calibrated.pkl`
- **Plots:** `risk_scorer/plots/` (ROC, PR, calibration, feature importance)
- **Key files:** `risk_scorer/feature_extractor.py`, `risk_scorer/data_generator.py`, `risk_scorer/train.py`, `risk_scorer/scorer.py`, `risk_scorer/evaluate.py`

**Task list:**
- [x] 4.1 — Add to requirements.txt: `xgboost==2.1.1`, `scikit-learn==1.5.2`, `matplotlib==3.9.2`, `joblib==1.4.2`
- [x] 4.2 — Create `risk_scorer/feature_extractor.py`
- [x] 4.3 — Create `risk_scorer/data_generator.py`
- [x] 4.4 — Create `risk_scorer/train.py`
- [x] 4.5 — Create `risk_scorer/scorer.py`
- [x] 4.6 — Create `risk_scorer/evaluate.py`

### ✅ Component 5: Triton + SageMaker Serving (DONE — scripts written, not executed)
- **Triton:** Python backend config + inference script (`serving/triton_model_repo/`)
- **Docker:** `serving/triton_compose.yml` + Prometheus metrics scrape config
- **Benchmark:** `serving/benchmark.py` — P50/P95/P99 latency via Triton HTTP API
- **SageMaker:** `serving/sagemaker_deploy.py` — packages model, uploads to S3, deploys endpoint
- **Note:** Triton not run locally (M3 ARM incompatibility + 8GB image). SageMaker not run (no AWS budget). Scripts ready for GPU machine / AWS deployment.

**Task list:**
- [x] 5.1 — `serving/export_model.py` — extract XGBoost + calibration params from pickle
- [x] 5.2 — `serving/triton_model_repo/risk_scorer/config.pbtxt` — Triton Python backend config
- [x] 5.3 — `serving/triton_model_repo/risk_scorer/1/model.py` — Triton inference script
- [x] 5.4 — `serving/triton_compose.yml` + `serving/prometheus.yml` — local Docker stack
- [x] 5.5 — `serving/benchmark.py` — latency benchmark (P50/P95/P99)
- [x] 5.6 — `serving/sagemaker_deploy.py` — SageMaker XGBoost endpoint deploy

### ✅ Component 6: Demo UI (DONE)
- **Stack:** React + TypeScript + Vite + Tailwind CSS + FastAPI backend
- **Features:**
  - Split-panel layout — note input left, results right
  - Auto mode detection (scores note quality 0-6, selects fast vs full)
  - Manual mode override (auto / fast / full)
  - SSE streaming progress box — live query-by-query pipeline updates
  - Stop button — cancel in-flight full mode inference
  - Glowing orb gauge — animated count-up, color shifts green→amber→red
  - Knowledge graph visualization — force-directed graph (react-force-graph-2d)
  - Dark / light theme toggle (light theme: warm cream Tennr-inspired)
  - Negation-aware feature extraction ("no suicidal ideation" → score 0)
  - Blended scoring (10% XGBoost + 90% linear) for score gradation
- **Model worker:** `serving/model_worker.py` — NL2Cypher as persistent subprocess (fixes MPS+asyncio deadlock)
- **Key files:** `app/app.py`, `frontend/src/`, `graphrag/worker_client.py`

**Task list:**
- [x] U1 — FastAPI backend with SSE streaming + auto mode detection
- [x] U2 — React + TypeScript + Vite + Tailwind setup
- [x] U3 — RiskGauge (glowing orb, animated count-up)
- [x] U4 — ResultPanel (recommendation, factor bars, mode info, graph context)
- [x] U5 — ProgressBox (live SSE event stream)
- [x] U6 — GraphView (force-directed knowledge graph)
- [x] U7 — Dark/light theme switcher
- [x] U8 — Stop button for cancelling full mode
- [x] U9 — Negation fix for suicidal ideation detection
- [x] U10 — Model worker subprocess (MPS+asyncio fix)

---

## Repo Structure
```
Init-Diagnose/
├── kg/                        # ontology, generators, loaders
│   ├── schema/ontology.py
│   ├── schema/constraints.cypher
│   ├── generators/node_generators.py
│   ├── generators/relationship_generators.py
│   └── loaders/neo4j_loader.py, verify.py
├── nl2graph/
│   ├── data/query_templates.py, nl_templates.py, training_data_gen.py
│   ├── train/train_qlora.py, lora_config.yaml, adapters/
│   └── inference/nl2cypher.py, schema_validator.py
├── graphrag/
│   ├── cypher_executor.py
│   ├── context_assembler.py
│   ├── retriever.py
│   ├── pipeline.py
│   └── worker_client.py       # subprocess worker client (MPS+asyncio fix)
├── risk_scorer/
│   ├── feature_extractor.py   # 16-dim feature extraction (2 paths)
│   ├── data_generator.py      # Neo4j → labeled training data
│   ├── train.py               # XGBoost + calibration training
│   ├── scorer.py              # inference: note + graph → risk score
│   ├── evaluate.py            # ROC, PR, calibration, importance plots
│   └── model/xgb_calibrated.pkl
├── serving/
│   ├── export_model.py        # extract XGBoost + calibration params
│   ├── model_worker.py        # persistent NL2Cypher subprocess
│   ├── triton_model_repo/
│   │   └── risk_scorer/
│   │       ├── config.pbtxt   # Python backend, batch=64, 2 CPU instances
│   │       └── 1/model.py     # Triton inference script
│   ├── triton_compose.yml     # Docker: Triton + Prometheus
│   ├── prometheus.yml         # metrics scrape config
│   ├── benchmark.py           # P50/P95/P99 latency benchmark
│   └── sagemaker_deploy.py    # AWS SageMaker endpoint deploy
├── app/
│   └── app.py                 # FastAPI backend + SSE streaming
├── frontend/
│   └── src/
│       ├── components/        # RiskGauge, ResultPanel, ProgressBox, GraphView
│       ├── App.tsx
│       ├── api.ts
│       └── types.ts
├── eval/nl2graph_eval.py
├── data/
│   ├── synthetic/             # gitignored
│   ├── nl2graph_train.jsonl
│   └── nl2graph_val.jsonl
├── models/                    # gitignored (too large)
├── docs/assets/               # screenshots + plots
├── docker-compose.yml
├── requirements.txt
└── .env                       # gitignored
```

---

## Environment
- **Python:** 3.13, venv at `.venv/`
- **Activate:** `source .venv/bin/activate`
- **Docker:** Neo4j running via `docker compose up -d`
- **Model:** Qwen2.5-3B downloads from HuggingFace on first run (~6GB, cached in HF cache)

---

## Key Decisions Made
1. **LLM:** Qwen2.5-3B-Instruct (no HF license gate, strong code gen)
2. **Fine-tune:** peft QLoRA on Colab T4 (mlx not viable for training on M3)
3. **Inference:** transformers + MPS on M3 (not mlx, avoids adapter conversion)
4. **Latency:** M3 inference ~26s/query — acceptable for demo, GPU target <150ms
5. **Validator:** always run fix() regardless of validation result
6. **Training data:** 1800 train / 200 val, 20 query templates × 5 NL variants

---

## Known Issues / Future Work
- NL2Graph FC at 85% (target 92%) — fix: retrain 336 steps + expand training data to 5K samples
- GraphRAG 3/6 queries fail — fix: improve Cypher generation + add retry logic
- Latency on M3 ~170s total — fix: deploy Triton on GPU (scripts ready in serving/)
- `generation_config.json` warnings (top_p/top_k) — cosmetic only, harmless

---

## Resume Instructions
1. `cd ~/Documents/Github/Init-Diagnose`
2. `source .venv/bin/activate`
3. `docker compose up -d` (start Neo4j)
4. All components complete — see Known Issues for future improvements
