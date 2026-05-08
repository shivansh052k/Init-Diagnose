import sys
import os
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from neo4j import GraphDatabase
from risk_scorer.feature_extractor import FeatureExtractor

load_dotenv()


class RiskDataGenerator:

    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "initdiagnose123")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.extractor = FeatureExtractor()

    def close(self):
        self.driver.close()

    def generate(self, n_patients: int = 5000, save_path: str = "data/risk_train.npz"):
        print(f"Querying Neo4j for {n_patients} patients...")
        records = self._query_patients(n_patients)
        print(f"  Got {len(records)} records")

        X, y = [], []
        for rec in records:
            features = self.extractor.from_graph_record(rec)
            label = self._label(rec)
            X.append(features)
            y.append(label)

        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int32)

        pos_rate = y.mean()
        print(f"  High-risk patients: {y.sum()} / {len(y)} ({pos_rate:.1%})")

        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        np.savez(save_path, X=X, y=y)
        print(f"  Saved → {save_path}")
        return X, y

    def _query_patients(self, limit: int) -> list[dict]:
        query = """
        MATCH (p:Patient)
        OPTIONAL MATCH (p)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
        OPTIONAL MATCH (p)-[:HAS_ASSESSMENT]->(a:Assessment)
        OPTIONAL MATCH (p)-[:HAS_EPISODE]->(e:Episode)
        OPTIONAL MATCH (p)-[:PRESCRIBED]->(m:Medication)
        OPTIONAL MATCH (p)-[pr:PRESENTS]->(s:Symptom)
        WITH p,
             collect(DISTINCT d.category) AS diagnosis_categories,
             collect(DISTINCT d.name)     AS diagnosis_names,
             [a2 IN collect(DISTINCT a) WHERE a2.type = 'PHQ-9'] AS phq9_assessments,
             [a2 IN collect(DISTINCT a) WHERE a2.type = 'GAF']   AS gaf_assessments,
             collect(DISTINCT e.severity) AS episode_severities,
             collect(DISTINCT e.type)     AS episode_types,
             collect(DISTINCT m.drug_class) AS drug_classes,
             collect({symptom: s.name, severity: pr.severity_score}) AS symptom_records,
             count(DISTINCT e) AS episode_count,
             count(DISTINCT d) AS diagnosis_count,
             count(DISTINCT m) AS medication_count
        RETURN p.patient_id AS patient_id,
               p.age        AS age,
               p.gender     AS gender,
               diagnosis_categories,
               diagnosis_names,
               phq9_assessments,
               gaf_assessments,
               episode_severities,
               episode_types,
               drug_classes,
               symptom_records,
               episode_count,
               diagnosis_count,
               medication_count
        LIMIT $limit
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(r) for r in result]

    def _label(self, record: dict) -> int:
        # Criterion 1: suicidal ideation severity >= 7
        for sym in (record.get("symptom_records") or []):
            if sym and sym.get("symptom") == "Suicidal ideation":
                if (sym.get("severity") or 0) >= 7:
                    return 1

        # Criterion 2: severe episode + psychotic or bipolar disorder
        severities = [s.lower() for s in (record.get("episode_severities") or [])]
        categories = [c.lower() for c in (record.get("diagnosis_categories") or [])]
        if "severe" in severities:
            if any(c in ["psychotic disorders", "bipolar disorders"] for c in categories):
                return 1

        # Criterion 3: PHQ-9 >= 20
        for a in (record.get("phq9_assessments") or []):
            if a and (a.get("score") or 0) >= 20:
                return 1

        # Criterion 4: schizophrenia/schizoaffective + any severe episode
        names = [n.lower() for n in (record.get("diagnosis_names") or [])]
        high_risk_dx = ["schizophrenia", "schizoaffective disorder", "bipolar i disorder"]
        if "severe" in severities and any(n in high_risk_dx for n in names):
            return 1

        return 0


if __name__ == "__main__":
    gen = RiskDataGenerator()
    try:
        gen.generate(n_patients=5000)
    finally:
        gen.close()