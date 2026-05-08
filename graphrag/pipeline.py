import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graphrag.retriever import GraphRAGRetriever


# Clinical note → structured questions mapping
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

        # Always include these baseline queries
        questions.append("What symptoms are associated with Major Depressive Disorder, severe?")
        questions.append("List all SSRI medications")

        return list(dict.fromkeys(questions))  # dedupe preserve order

    def run(self, clinical_note: str) -> dict:
        t0 = time.time()

        questions = self.extract_clinical_questions(clinical_note)
        retrievals = []

        for i, q in enumerate(questions, 1):
            print(f"  [{i}/{len(questions)}] {q[:60]}")
            result = self.retriever.retrieve(q)
            retrievals.append(result)

        # Assemble full context
        context_blocks = []
        for r in retrievals:
            if r["exec_success"] and r["record_count"] > 0:
                context_blocks.append(r["context"])

        full_context = "\n\n".join(context_blocks)

        total_latency = (time.time() - t0) * 1000

        return {
            "clinical_note": clinical_note,
            "questions_generated": questions,
            "retrievals": retrievals,
            "full_context": full_context,
            "total_queries": len(questions),
            "successful_queries": sum(1 for r in retrievals if r["exec_success"]),
            "total_records": sum(r["record_count"] for r in retrievals),
            "total_latency_ms": round(total_latency, 2),
        }


if __name__ == "__main__":
    pipeline = GraphRAGPipeline()

    clinical_note = """
    Patient presents with persistent depressed mood for 6 weeks, 
    anhedonia, insomnia, and fatigue. PHQ-9 score of 18. 
    History of Major Depressive Disorder. Currently on Sertraline 50mg.
    No suicidal ideation reported. GAF score 55.
    """

    print("── GraphRAG Pipeline Test ──────────────────────────")
    print(f"Clinical Note: {clinical_note.strip()[:100]}...")

    result = pipeline.run(clinical_note)

    print(f"\nQueries generated: {result['total_queries']}")
    print(f"Successful:        {result['successful_queries']}")
    print(f"Total records:     {result['total_records']}")
    print(f"Total latency:     {result['total_latency_ms']}ms")
    print(f"\nContext preview:\n{result['full_context'][:500]}")

    pipeline.close()