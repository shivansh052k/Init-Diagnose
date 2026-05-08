import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "synthetic"
BATCH_SIZE = 500


def load_json(name: str) -> list[dict]:
    with open(DATA_DIR / f"{name}.json") as f:
        return json.load(f)


class KGLoader:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")),
        )

    def close(self):
        self.driver.close()

    def apply_constraints(self):
        constraints_path = Path(__file__).parent.parent / "schema" / "constraints.cypher"
        with open(constraints_path) as f:
            statements = [s.strip() for s in f.read().split(";") if s.strip()]
        with self.driver.session() as session:
            for stmt in statements:
                if stmt:
                    session.run(stmt)
        print("Constraints + indexes applied.")

    def batch_run(self, session, query: str, data: list[dict]):
        for i in range(0, len(data), BATCH_SIZE):
            session.run(query, batch=data[i:i + BATCH_SIZE])

    def load_nodes(self):
        with self.driver.session() as s:
            print("Loading patients...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Patient {patient_id:r.patient_id, age:r.age, gender:r.gender, admission_date:r.admission_date, discharge_date:r.discharge_date, insurance_type:r.insurance_type})",
                load_json("patients"))

            print("Loading diagnoses...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Diagnosis {diagnosis_id:r.diagnosis_id, dsm5_code:r.dsm5_code, name:r.name, category:r.category, severity:r.severity})",
                load_json("diagnoses"))

            print("Loading symptoms...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Symptom {symptom_id:r.symptom_id, name:r.name, domain:r.domain, severity_scale:r.severity_scale})",
                load_json("symptoms"))

            print("Loading medications...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Medication {medication_id:r.medication_id, name:r.name, drug_class:r.drug_class, mechanism:r.mechanism, typical_dosage:r.typical_dosage})",
                load_json("medications"))

            print("Loading clinicians...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Clinician {clinician_id:r.clinician_id, specialty:r.specialty, years_experience:r.years_experience, board_certified:r.board_certified})",
                load_json("clinicians"))

            print("Loading assessments...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Assessment {assessment_id:r.assessment_id, type:r.type, score:r.score, date:r.date, interpretation:r.interpretation})",
                load_json("assessments"))

            print("Loading episodes...")
            self.batch_run(s,
                "UNWIND $batch AS r CREATE (:Episode {episode_id:r.episode_id, type:r.type, severity:r.severity, start_date:r.start_date, end_date:r.end_date})",
                load_json("episodes"))

        print("All nodes loaded.")

    def load_relationships(self):
        with self.driver.session() as s:
            print("Loading HAS_DIAGNOSIS...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (d:Diagnosis {diagnosis_id:r.diagnosis_id}) CREATE (p)-[:HAS_DIAGNOSIS {date_diagnosed:r.date_diagnosed, is_primary:r.is_primary}]->(d)",
                load_json("rel_HAS_DIAGNOSIS"))

            print("Loading PRESENTS...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (s:Symptom {symptom_id:r.symptom_id}) CREATE (p)-[:PRESENTS {severity_score:r.severity_score, reported_date:r.reported_date}]->(s)",
                load_json("rel_PRESENTS"))

            print("Loading PRESCRIBED...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (m:Medication {medication_id:r.medication_id}) CREATE (p)-[:PRESCRIBED {dosage:r.dosage, start_date:r.start_date, active:r.active}]->(m)",
                load_json("rel_PRESCRIBED"))

            print("Loading ASSESSED_BY...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (c:Clinician {clinician_id:r.clinician_id}) CREATE (p)-[:ASSESSED_BY {assessment_date:r.assessment_date}]->(c)",
                load_json("rel_ASSESSED_BY"))

            print("Loading HAS_EPISODE...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (e:Episode {episode_id:r.episode_id}) CREATE (p)-[:HAS_EPISODE]->(e)",
                load_json("rel_HAS_EPISODE"))

            print("Loading HAS_ASSESSMENT...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (p:Patient {patient_id:r.patient_id}), (a:Assessment {assessment_id:r.assessment_id}) CREATE (p)-[:HAS_ASSESSMENT {administered_by:r.administered_by}]->(a)",
                load_json("rel_HAS_ASSESSMENT"))

            print("Loading HAS_SYMPTOM...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (d:Diagnosis {diagnosis_id:r.diagnosis_id}), (s:Symptom {symptom_id:r.symptom_id}) CREATE (d)-[:HAS_SYMPTOM {frequency:r.frequency}]->(s)",
                load_json("rel_HAS_SYMPTOM"))

            print("Loading TREATED_BY...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (d:Diagnosis {diagnosis_id:r.diagnosis_id}), (m:Medication {medication_id:r.medication_id}) CREATE (d)-[:TREATED_BY {evidence_level:r.evidence_level}]->(m)",
                load_json("rel_TREATED_BY"))

            print("Loading LINKED_TO...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (e:Episode {episode_id:r.episode_id}), (d:Diagnosis {diagnosis_id:r.diagnosis_id}) CREATE (e)-[:LINKED_TO]->(d)",
                load_json("rel_LINKED_TO"))

            print("Loading TREATS...")
            self.batch_run(s,
                "UNWIND $batch AS r MATCH (c:Clinician {clinician_id:r.clinician_id}), (p:Patient {patient_id:r.patient_id}) CREATE (c)-[:TREATS]->(p)",
                load_json("rel_TREATS"))

        print("All relationships loaded.")


if __name__ == "__main__":
    loader = KGLoader()
    try:
        loader.apply_constraints()
        loader.load_nodes()
        loader.load_relationships()
    finally:
        loader.close()
    print("\nKG load complete.")