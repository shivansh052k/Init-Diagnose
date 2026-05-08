import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nl2graph.data.query_templates import QUERY_TEMPLATES
from nl2graph.data.nl_templates import NL_TEMPLATES

random.seed(42)

# ── Fill values for template params ───────────────────────────────────────────

FILL_VALUES = {
    "diagnosis_name": [
        "Major Depressive Disorder, moderate",
        "Major Depressive Disorder, severe",
        "Generalized Anxiety Disorder",
        "Bipolar I Disorder",
        "Bipolar II Disorder",
        "PTSD",
        "Schizophrenia",
        "Panic Disorder",
        "OCD",
        "Borderline Personality Disorder",
        "ADHD, combined type",
        "Schizoaffective Disorder",
    ],
    "medication_name": [
        "Sertraline", "Fluoxetine", "Escitalopram",
        "Venlafaxine", "Lithium", "Quetiapine",
        "Aripiprazole", "Methylphenidate", "Clonazepam",
        "Valproate", "Mirtazapine", "Bupropion",
    ],
    "symptom_name": [
        "Depressed mood", "Anhedonia", "Insomnia",
        "Suicidal ideation", "Hallucinations", "Panic attacks",
        "Fatigue", "Poor concentration", "Irritability",
        "Hypervigilance", "Flashbacks", "Emotional dysregulation",
    ],
    "specialty": [
        "General Psychiatry", "Child Psychiatry",
        "Addiction Psychiatry", "Forensic Psychiatry",
        "Geriatric Psychiatry", "Neuropsychiatry",
    ],
    "drug_class": [
        "SSRI", "SNRI", "Mood Stabilizer",
        "Atypical Antipsychotic", "Benzodiazepine",
        "Stimulant", "NDRI",
    ],
    "episode_type": [
        "Manic", "Depressive", "Mixed",
        "Psychotic", "Hypomanic", "Anxious",
    ],
    "insurance_type": ["Private", "Medicare", "Medicaid", "Uninsured"],
    "category": [
        "Mood Disorders", "Anxiety Disorders", "Psychotic Disorders",
        "Bipolar Disorders", "Trauma Disorders", "Substance Disorders",
        "Personality Disorders", "Neurodevelopmental",
    ],
    "domain": [
        "Affective", "Cognitive", "Behavioral",
        "Somatic", "Anxiety", "Psychotic", "Sleep",
    ],
    "threshold": [5, 10, 15, 20, 7, 8, 3],
    "min_age": [18, 25, 30, 40, 50, 60],
    "max_age": [30, 45, 60, 75, 85],
    "patient_id": ["PLACEHOLDER_ID"],
    "diagnosis_1": [
        "Major Depressive Disorder, moderate",
        "Generalized Anxiety Disorder",
        "Bipolar I Disorder",
        "PTSD",
    ],
    "diagnosis_2": [
        "Generalized Anxiety Disorder",
        "Panic Disorder",
        "Borderline Personality Disorder",
        "ADHD, combined type",
    ],
}

SYSTEM_PROMPT = (
    "You are an ontology-safe Cypher query generator for a psychiatry knowledge graph in Neo4j. "
    "Only use nodes, relationships, and properties defined in the schema below.\n\n"
    "NODES:\n"
    "- Patient {patient_id, age, gender, admission_date, discharge_date, insurance_type}\n"
    "- Diagnosis {diagnosis_id, dsm5_code, name, category, severity}\n"
    "- Symptom {symptom_id, name, domain, severity_scale}\n"
    "- Medication {medication_id, name, drug_class, mechanism, typical_dosage}\n"
    "- Clinician {clinician_id, specialty, years_experience, board_certified}\n"
    "- Assessment {assessment_id, type, score, date, interpretation}\n"
    "- Episode {episode_id, type, severity, start_date, end_date}\n\n"
    "RELATIONSHIPS:\n"
    "- (Patient)-[:HAS_DIAGNOSIS {date_diagnosed, is_primary}]->(Diagnosis)\n"
    "- (Patient)-[:PRESENTS {severity_score, reported_date}]->(Symptom)\n"
    "- (Patient)-[:PRESCRIBED {dosage, start_date, active}]->(Medication)\n"
    "- (Patient)-[:ASSESSED_BY {assessment_date}]->(Clinician)\n"
    "- (Patient)-[:HAS_EPISODE]->(Episode)\n"
    "- (Patient)-[:HAS_ASSESSMENT {administered_by}]->(Assessment)\n"
    "- (Diagnosis)-[:HAS_SYMPTOM {frequency}]->(Symptom)\n"
    "- (Diagnosis)-[:TREATED_BY {evidence_level}]->(Medication)\n"
    "- (Episode)-[:LINKED_TO]->(Diagnosis)\n"
    "- (Clinician)-[:TREATS]->(Patient)\n\n"
    "RULES:\n"
    "1. Only MATCH existing schema nodes and relationships.\n"
    "2. Always RETURN meaningful properties, not full nodes.\n"
    "3. Use WHERE for filters, not inline property maps when filtering on multiple conditions.\n"
    "4. Never use MERGE or CREATE.\n"
    "5. For aggregations use WITH before ORDER BY.\n"
    "6. Patient.insurance_type values: Private, Medicare, Medicaid, Uninsured.\n"
    "7. Episode.type values: Manic, Depressive, Mixed, Psychotic, Hypomanic, Anxious.\n"
    "8. Assessment.type values: PHQ-9, GAF, HAM-A, MADRS, PANSS, AUDIT, PCL-5, YMRS.\n\n"
    "EXAMPLES:\n"
    "Q: Find patients with Major Depressive Disorder, severe\n"
    "A: MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {name: 'Major Depressive Disorder, severe'}) "
    "RETURN p.patient_id, p.age, p.gender\n\n"
    "Q: What medications treat Bipolar I Disorder?\n"
    "A: MATCH (d:Diagnosis {name: 'Bipolar I Disorder'})-[:TREATED_BY]->(m:Medication) "
    "RETURN m.name, m.drug_class, m.mechanism\n\n"
    "Q: Find patients with PHQ-9 score above 15\n"
    "A: MATCH (p:Patient)-[:HAS_ASSESSMENT]->(a:Assessment {type: 'PHQ-9'}) "
    "WHERE a.score >= 15 RETURN p.patient_id, a.score, a.interpretation\n\n"
    "Q: Find patients with comorbid PTSD and Generalized Anxiety Disorder\n"
    "A: MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d1:Diagnosis {name: 'PTSD'}), "
    "(p)-[:HAS_DIAGNOSIS]->(d2:Diagnosis {name: 'Generalized Anxiety Disorder'}) "
    "RETURN p.patient_id, p.age\n\n"
    "Output only the Cypher query, no explanation."
)


def fill_template(template: str, params: list[str]) -> dict | None:
    values = {}
    for param in params:
        if param not in FILL_VALUES:
            return None
        values[param] = random.choice(FILL_VALUES[param])
    try:
        filled = template.format(**values)
        return {"cypher": filled, "values": values}
    except KeyError:
        return None


def build_chat_sample(nl: str, cypher: str) -> dict:
    return {
        "text": (
            f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            f"<|im_start|>user\n{nl}<|im_end|>\n"
            f"<|im_start|>assistant\n{cypher}<|im_end|>"
        )
    }


def generate_dataset(n_samples: int = 2000) -> list[dict]:
    samples = []
    template_map = {t["id"]: t for t in QUERY_TEMPLATES}

    while len(samples) < n_samples:
        qid = random.choice(list(NL_TEMPLATES.keys()))
        nl_variants = NL_TEMPLATES[qid]
        qt = template_map[qid]

        result = fill_template(qt["cypher"], qt["params"])
        if result is None:
            continue

        nl_template = random.choice(nl_variants)
        try:
            nl = nl_template.format(**result["values"])
        except KeyError:
            continue

        samples.append(build_chat_sample(nl, result["cypher"]))

    return samples


def save_splits(samples: list[dict], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    random.shuffle(samples)

    split = int(len(samples) * 0.9)
    train = samples[:split]
    val = samples[split:]

    for name, data in [("train", train), ("val", val)]:
        path = output_dir / f"nl2graph_{name}.jsonl"
        with open(path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        print(f"  saved {len(data):>5,} samples → {path}")


if __name__ == "__main__":
    print("Generating NL2Graph training data...")
    samples = generate_dataset(2000)
    save_splits(samples, Path(__file__).parent.parent.parent / "data")
    print("Done.")