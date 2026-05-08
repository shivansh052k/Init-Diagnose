import re
import numpy as np

FEATURE_NAMES = [
    "age_norm",
    "gender_female",
    "gender_nonbinary",
    "num_diagnoses",
    "has_mood_disorder",
    "has_anxiety_disorder",
    "has_psychotic_disorder",
    "has_bipolar_disorder",
    "has_personality_disorder",
    "suicidal_ideation_severity",
    "phq9_norm",
    "gaf_risk",
    "num_medications",
    "has_antipsychotic",
    "has_severe_episode",
    "episode_count_norm",
]

_ANTIPSYCHOTICS = {"atypical antipsychotic", "typical antipsychotic"}
_MOOD_STABILIZERS = {"mood stabilizer"}
_BENZO = {"benzodiazepine"}

_PSYCHOTIC_KEYWORDS = ["psycho", "hallucin", "delusion", "schizo", "schizoaffective"]
_BIPOLAR_KEYWORDS = ["bipolar", "manic", "mania", "hypomanic"]
_MOOD_KEYWORDS = ["depress", "mood disorder", "dysthymia"]
_ANXIETY_KEYWORDS = ["anxiety", "panic", "worry", "gad", "phobia", "ocd"]
_PERSONALITY_KEYWORDS = ["borderline", "personality disorder", "bpd"]
_SUICIDAL_KEYWORDS = ["suicid", "self-harm", "kill himself", "kill herself", "end his life", "end her life"]
_SEVERE_KEYWORDS = ["severe", "acute", "critical", "imminent", "hospitali"]
_ANTIPSYCHOTIC_DRUGS = ["quetiapine", "risperidone", "aripiprazole", "olanzapine", "haloperidol", "clozapine"]


class FeatureExtractor:

    def from_graph_record(self, record: dict) -> np.ndarray:
        """Extract features from a Neo4j query result row (training path)."""
        age = record.get("age", 40)
        gender = (record.get("gender") or "").lower()
        categories = [c.lower() for c in (record.get("diagnosis_categories") or [])]
        phq9_list = record.get("phq9_assessments") or []
        gaf_list = record.get("gaf_assessments") or []
        episode_severities = [s.lower() for s in (record.get("episode_severities") or [])]
        drug_classes = [d.lower() for d in (record.get("drug_classes") or [])]
        symptom_records = record.get("symptom_records") or []
        episode_count = record.get("episode_count") or 0
        diagnosis_count = record.get("diagnosis_count") or 0
        medication_count = record.get("medication_count") or 0

        suicidal_severity = 0.0
        for sym in symptom_records:
            if sym and sym.get("symptom") == "Suicidal ideation":
                suicidal_severity = float(sym.get("severity") or 0)
                break

        phq9 = 0.0
        if phq9_list:
            scores = [a["score"] for a in phq9_list if a and a.get("score") is not None]
            if scores:
                phq9 = max(scores)

        gaf = 50.0
        if gaf_list:
            scores = [a["score"] for a in gaf_list if a and a.get("score") is not None]
            if scores:
                gaf = min(scores)

        return np.array([
            min(age, 85) / 85.0,
            1.0 if "female" in gender else 0.0,
            1.0 if "non-binary" in gender else 0.0,
            min(diagnosis_count, 5) / 5.0,
            1.0 if any("mood" in c for c in categories) else 0.0,
            1.0 if any("anxiety" in c for c in categories) else 0.0,
            1.0 if any("psychotic" in c for c in categories) else 0.0,
            1.0 if any("bipolar" in c for c in categories) else 0.0,
            1.0 if any("personality" in c for c in categories) else 0.0,
            suicidal_severity / 10.0,
            phq9 / 27.0,
            1.0 - (gaf / 100.0),
            min(medication_count, 5) / 5.0,
            1.0 if any(d in _ANTIPSYCHOTICS for d in drug_classes) else 0.0,
            1.0 if "severe" in episode_severities else 0.0,
            min(episode_count, 4) / 4.0,
        ], dtype=np.float32)

    def from_clinical_context(self, note: str, graphrag: dict) -> np.ndarray:
        """Extract features from clinical note text + GraphRAG output (inference path)."""
        note_lower = note.lower()
        context_lower = (graphrag.get("full_context") or "").lower()
        combined = note_lower + " " + context_lower

        age = self._extract_number(note_lower, r"(\d{2,3})[- ]year") or 40
        gender_female = 1.0 if any(w in note_lower for w in ["female", "woman", "she ", "her "]) else 0.0
        gender_nb = 1.0 if any(w in note_lower for w in ["non-binary", "nonbinary", "they ", "them "]) else 0.0

        has_mood = 1.0 if any(w in combined for w in _MOOD_KEYWORDS) else 0.0
        has_anxiety = 1.0 if any(w in combined for w in _ANXIETY_KEYWORDS) else 0.0
        has_psychotic = 1.0 if any(w in combined for w in _PSYCHOTIC_KEYWORDS) else 0.0
        has_bipolar = 1.0 if any(w in combined for w in _BIPOLAR_KEYWORDS) else 0.0
        has_personality = 1.0 if any(w in combined for w in _PERSONALITY_KEYWORDS) else 0.0

        # check negation — "no suicidal", "denies suicidal", "without suicidal"
        _NEGATIONS = ["no suicidal", "denies suicidal", "without suicidal",
                     "no self-harm", "denies self-harm", "no active suicidal","no si", "si: none", "si: denied",
                     ]
        negated = any(n in combined for n in _NEGATIONS) or \
            bool(re.search(r"(no|denies|without|denying|denied)\s+\w*\s*(suicid|self.harm)", combined))
        suicidal = 0.0 if negated else (1.0 if any(w in combined for w in _SUICIDAL_KEYWORDS) else 0.0)

        phq9 = self._extract_number(note_lower, r"phq[-\s]?9[^\d]{0,10}(\d+)") or 0.0
        gaf = self._extract_number(note_lower, r"gaf[^\d]{0,10}(\d+)") or 50.0

        med_count = sum(1 for d in _ANTIPSYCHOTIC_DRUGS if d in note_lower)
        has_antipsychotic = 1.0 if med_count > 0 or any(w in note_lower for w in ["antipsychotic", "quetiapine", "risperidone", "aripiprazole", "olanzapine"]) else 0.0

        _SEVERE_NEGATIONS = ["no severe", "not severe", "without severe"]
        has_severe = 0.0 if any(n in combined for n in _SEVERE_NEGATIONS) else (1.0 if any(w in combined for w in _SEVERE_KEYWORDS) else 0.0)

        total_q = graphrag.get("total_queries") or 1
        successful_q = graphrag.get("successful_queries") or 0
        episode_count_norm = min(successful_q / max(total_q, 1), 1.0)

        return np.array([
            min(age, 85) / 85.0,
            gender_female,
            gender_nb,
            min(sum([has_mood, has_anxiety, has_psychotic, has_bipolar, has_personality]), 5) / 5.0,
            has_mood,
            has_anxiety,
            has_psychotic,
            has_bipolar,
            has_personality,
            suicidal,
            min(phq9, 27) / 27.0,
            1.0 - (min(gaf, 100) / 100.0),
            min(med_count, 5) / 5.0,
            has_antipsychotic,
            has_severe,
            episode_count_norm,
        ], dtype=np.float32)

    def _extract_number(self, text: str, pattern: str) -> float | None:
        m = re.search(pattern, text)
        if m:
            try:
                return float(m.group(1))
            except (ValueError, IndexError):
                return None
        return None