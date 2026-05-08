import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graphrag.cypher_executor import CypherExecutor
from graphrag.context_assembler import ContextAssembler
from graphrag.worker_client import WorkerClient


class GraphRAGRetriever:
    def __init__(self):
        print("Initializing GraphRAG Retriever...")
        self.nl2cypher = WorkerClient()
        self.executor = CypherExecutor()
        self.assembler = ContextAssembler()
        print("Retriever ready.")

    def close(self):
        self.nl2cypher.close()
        self.executor.close()

    def retrieve(self, question: str) -> dict:
        t0 = time.time()

        # Step 1: NL → Cypher
        nl_result = self.nl2cypher.generate(question)
        cypher = nl_result["cypher"]
        nl_latency = nl_result["latency_ms"]

        # Step 2: Execute Cypher
        exec_result = self.executor.execute_safe(cypher)
        exec_latency = exec_result["latency_ms"]

        # Step 3: Assemble context
        context = self.assembler.assemble(
            question, cypher, exec_result["records"]
        )

        total_latency = (time.time() - t0) * 1000

        return {
            "question": question,
            "cypher": cypher,
            "cypher_valid": nl_result.get("valid", True),
            "cypher_was_fixed": nl_result.get("cypher_was_fixed", False),
            "records": exec_result["records"],
            "record_count": exec_result["count"],
            "context": context,
            "exec_success": exec_result["success"],
            "exec_error": exec_result["error"],
            "nl_latency_ms": nl_latency,
            "exec_latency_ms": exec_latency,
            "total_latency_ms": round(total_latency, 2),
        }


if __name__ == "__main__":
    retriever = GraphRAGRetriever()

    questions = [
        "Find patients with Major Depressive Disorder, severe",
        "What medications treat Bipolar I Disorder?",
        "Find patients with PHQ-9 score above 15",
    ]

    print("\n── GraphRAG Retriever Test ─────────────────────────")
    for q in questions:
        print(f"\nQ: {q}")
        result = retriever.retrieve(q)
        print(f"Cypher:    {result['cypher'][:80]}")
        print(f"Records:   {result['record_count']}")
        print(f"NL ms:     {result['nl_latency_ms']}")
        print(f"Exec ms:   {result['exec_latency_ms']}")
        print(f"Total ms:  {result['total_latency_ms']}")
        print(f"Context:\n{result['context'][:300]}")

    retriever.close()