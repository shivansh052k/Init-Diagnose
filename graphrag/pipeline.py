import sys
import time
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from graphrag.retriever import GraphRAGRetriever

TRIAGE_QUESTIONS = [
    "What is the primary diagnosis for this patient?",
    "What symptoms does this patient present with?",
    "What medications is this patient prescribed?",
    "What is the PHQ-9 score for this patient?",
    "Does this patient have any severe episodes?",
]


class GraphRAGPipeline:

    def __init__(self):
        self.retriever = GraphRAGRetriever()

    def close(self):
        self.retriever.close()

    def extract_clinical_questions(self, clinical_note: str) -> list[str]:
        questions = []
        note_lower = clinical_note.lower()

        if any(w in note_lower for w in ["depress", "mood", "bipolar", "manic"]):
            questions.append("Find patients with Mood Disorders diagnoses")
            questions.append("What medications treat Major Depressive Disorder, severe?")

        if any(w in note_lower for w in ["anxiety", "panic", "worry", "fear"]):
            questions.append("Find patients with Anxiety Disorders diagnoses")
            questions.append("What medications treat Generalized Anxiety Disorder?")

        if any(w in note_lower for w in ["psycho", "hallucin", "delusion", "schizo"]):
            questions.append("Find patients with Psychotic Disorders diagnoses")
            questions.append("What medications treat Schizophrenia?")

        if any(w in note_lower for w in ["suicid", "self-harm", "harm"]):
            questions.append("Find patients with suicidal ideation severity above 7")

        if any(w in note_lower for w in ["ptsd", "trauma", "flashback"]):
            questions.append("Find patients diagnosed with PTSD")

        if any(w in note_lower for w in ["phq", "score", "assessment", "screen"]):
            questions.append("Find patients with PHQ-9 score above 15")

        questions.append("What symptoms are associated with Major Depressive Disorder, severe?")
        questions.append("List all SSRI medications")

        return list(dict.fromkeys(questions))

    def run(self, clinical_note: str, progress_callback: Callable | None = None) -> dict:
        def emit(msg: str, step: str = "info", current: int = 0, total: int = 0):
            if progress_callback:
                progress_callback({
                    "type": "progress",
                    "step": step,
                    "msg": msg,
                    "current": current,
                    "total": total,
                })

        t0 = time.time()

        emit("Extracting clinical questions from note...", "info")
        questions = self.extract_clinical_questions(clinical_note)
        emit(f"Generated {len(questions)} queries", "info")

        retrievals = []
        for i, q in enumerate(questions, 1):
            emit(f"Query {i}/{len(questions)}: {q[:60]}", "query", i, len(questions))
            t_q = time.time()
            result = self.retriever.retrieve(q)
            elapsed = round((time.time() - t_q) * 1000)

            if result["exec_success"]:
                emit(f"  ✓ {result['record_count']} records ({elapsed}ms)", "success", i, len(questions))
            else:
                emit(f"  ✗ Query failed ({elapsed}ms)", "error", i, len(questions))

            retrievals.append(result)

        emit("Assembling graph context...", "info")
        context_blocks = [
            r["context"] for r in retrievals
            if r["exec_success"] and r["record_count"] > 0
        ]
        full_context = "\n\n".join(context_blocks)

        total_latency = (time.time() - t0) * 1000
        emit(f"GraphRAG complete — {total_latency:.0f}ms", "done")

        return {
            "clinical_note":       clinical_note,
            "questions_generated": questions,
            "retrievals":          retrievals,
            "full_context":        full_context,
            "total_queries":       len(questions),
            "successful_queries":  sum(1 for r in retrievals if r["exec_success"]),
            "total_records":       sum(r["record_count"] for r in retrievals),
            "total_latency_ms":    round(total_latency, 2),
        }


if __name__ == "__main__":
    pipeline = GraphRAGPipeline()
    clinical_note = """
    Patient presents with persistent depressed mood for 6 weeks,
    anhedonia, insomnia, and fatigue. PHQ-9 score of 18.
    History of Major Depressive Disorder. Currently on Sertraline 50mg.
    No suicidal ideation reported. GAF score 55.
    """
    result = pipeline.run(clinical_note, progress_callback=print)
    print(f"Latency: {result['total_latency_ms']}ms")
    pipeline.close()