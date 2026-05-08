import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from nl2graph.inference.schema_validator import SchemaValidator

ADAPTER_PATH = str(Path(__file__).parent.parent / "train" / "adapters")
BASE_MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"

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


class NL2Cypher:
    def __init__(self):
        if os.environ.get("FORCE_CPU") == "1":
            self.device = "cpu"
        else:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Loading model on {self.device}...")
        
        self.validator = SchemaValidator()

        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            torch_dtype=torch.float16,
            device_map=self.device,
        )
        self.model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
        self.model.eval()
        print("Model ready.")

    def generate(self, question: str, max_new_tokens: int = 200) -> dict:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

        t0 = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )
        latency_ms = (time.time() - t0) * 1000

        generated = outputs[0][inputs["input_ids"].shape[1]:]
        cypher = self.tokenizer.decode(generated, skip_special_tokens=True).strip()


        validator = self.validator
        validation = validator.validate_and_fix(cypher)

        return {
            "question": question,
            "cypher": validation["fixed"],
            "cypher_was_fixed": validation["was_fixed"],
            "valid": validation["valid"],
            "errors": validation["errors"],
            "latency_ms": round(latency_ms, 2),
        }


if __name__ == "__main__":
    nl2cypher = NL2Cypher()
    

    test_questions = [
        "Find all patients diagnosed with Major Depressive Disorder, severe",
        "What medications are used to treat Bipolar I Disorder?",
        "Find patients with PHQ-9 score above 15",
        "Which patients have comorbid PTSD and Generalized Anxiety Disorder?",
        "Show patients with severe Manic episodes",
    ]

    print("\n── NL2Cypher Test ─────────────────────────────────────")
    for q in test_questions:
        result = nl2cypher.generate(q)
        print(f"\nQ: {result['question']}")
        print(f"Cypher: {result['cypher']}")
        print(f"Latency: {result['latency_ms']}ms")