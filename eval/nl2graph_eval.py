import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from nl2graph.inference.nl2cypher import NL2Cypher

GOLD_SET = [
    {"question": "Find all patients diagnosed with Major Depressive Disorder, severe", "expected_pattern": ["HAS_DIAGNOSIS", "Diagnosis", "Major Depressive Disorder"]},
    {"question": "What medications are used to treat Bipolar I Disorder?", "expected_pattern": ["TREATED_BY", "Medication", "Bipolar I Disorder"]},
    {"question": "Find patients with PHQ-9 score above 15", "expected_pattern": ["HAS_ASSESSMENT", "PHQ-9", "score"]},
    {"question": "Which patients have comorbid PTSD and Generalized Anxiety Disorder?", "expected_pattern": ["HAS_DIAGNOSIS", "PTSD", "Generalized Anxiety Disorder"]},
    {"question": "Show patients with severe Manic episodes", "expected_pattern": ["HAS_EPISODE", "Manic", "Severe"]},
    {"question": "List all SSRI medications", "expected_pattern": ["Medication", "SSRI"]},
    {"question": "Find patients with suicidal ideation severity above 7", "expected_pattern": ["PRESENTS", "Suicidal ideation", "severity_score"]},
    {"question": "Show board certified General Psychiatry clinicians", "expected_pattern": ["Clinician", "General Psychiatry", "board_certified"]},
    {"question": "Count patients per diagnosis category", "expected_pattern": ["HAS_DIAGNOSIS", "category", "count"]},
    {"question": "Find patients aged 18 to 30 with Generalized Anxiety Disorder", "expected_pattern": ["HAS_DIAGNOSIS", "age", "Generalized Anxiety Disorder"]},
    {"question": "What symptoms are associated with Schizophrenia?", "expected_pattern": ["HAS_SYMPTOM", "Symptom", "Schizophrenia"]},
    {"question": "Find patients on active Lithium prescription", "expected_pattern": ["PRESCRIBED", "Lithium", "active"]},
    {"question": "Show patients with GAF score below 40", "expected_pattern": ["HAS_ASSESSMENT", "GAF", "score"]},
    {"question": "Find patients whose primary diagnosis is Bipolar I Disorder", "expected_pattern": ["HAS_DIAGNOSIS", "is_primary", "Bipolar I Disorder"]},
    {"question": "List patients with Psychotic symptoms", "expected_pattern": ["PRESENTS", "Symptom", "Psychotic"]},
    {"question": "Find Medicare patients with Mood Disorders", "expected_pattern": ["Patient", "Medicare", "Mood Disorders"]},
    {"question": "Show average PHQ-9 score per diagnosis", "expected_pattern": ["HAS_ASSESSMENT", "PHQ-9", "avg"]},
    {"question": "Find patients treated by Addiction Psychiatry clinicians", "expected_pattern": ["TREATS", "Addiction Psychiatry"]},
    {"question": "List patients with severe Depressive episodes", "expected_pattern": ["HAS_EPISODE", "Depressive", "Severe"]},
    {"question": "What is the mechanism of Quetiapine?", "expected_pattern": ["Medication", "Quetiapine", "mechanism"]},
]


def functional_correct(cypher: str, patterns: list[str]) -> bool:
    cypher_upper = cypher.upper()
    return all(p.upper() in cypher_upper for p in patterns)


def run_eval(n_questions: int = 20):
    nl2cypher = NL2Cypher()

    results = []
    correct = 0
    total_latency = 0

    print(f"\nRunning eval on {n_questions} questions...\n")

    for i, item in enumerate(GOLD_SET[:n_questions]):
        result = nl2cypher.generate(item["question"])
        is_correct = functional_correct(result["cypher"], item["expected_pattern"])

        if is_correct:
            correct += 1

        total_latency += result["latency_ms"]

        status = "PASS" if is_correct else "FAIL"
        print(f"[{status}] Q{i+1}: {item['question'][:60]}")
        if not is_correct:
            print(f"       Cypher: {result['cypher'][:100]}")

        results.append({
            "question": item["question"],
            "cypher": result["cypher"],
            "correct": is_correct,
            "latency_ms": result["latency_ms"],
            "was_fixed": result.get("cypher_was_fixed", False),
        })

    accuracy = correct / n_questions * 100
    avg_latency = total_latency / n_questions

    print(f"\n── Results ─────────────────────────────────")
    print(f"  Functional Correctness: {correct}/{n_questions} ({accuracy:.1f}%)")
    print(f"  Avg Latency:            {avg_latency:.0f}ms")
    print(f"  Target Correctness:     92%")
    print(f"  Target Latency:         <150ms")

    output_path = Path(__file__).parent / "nl2graph_eval_results.json"
    with open(output_path, "w") as f:
        json.dump({
            "accuracy": accuracy,
            "avg_latency_ms": avg_latency,
            "correct": correct,
            "total": n_questions,
            "results": results,
        }, f, indent=2)
    print(f"\n  Results saved → {output_path}")


if __name__ == "__main__":
    run_eval()