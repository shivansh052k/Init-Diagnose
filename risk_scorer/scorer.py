import sys
import joblib
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from risk_scorer.feature_extractor import FeatureExtractor, FEATURE_NAMES

MODEL_PATH = Path(__file__).parent / "model" / "xgb_calibrated.pkl"

TRIAGE_THRESHOLDS = {
    "High":   0.65,
    "Medium": 0.35,
    "Low":    0.0,
}


class RiskScorer:

    def __init__(self, model_path: str | Path = MODEL_PATH):
        self.model = joblib.load(model_path)
        self.extractor = FeatureExtractor()

    def score(self, note: str, graphrag: dict) -> dict:
        features = self.extractor.from_clinical_context(note, graphrag)
        prob = float(self.model.predict_proba(features.reshape(1, -1))[0, 1])
        triage = self._triage_level(prob)
        top_factors = self._top_factors(features)

        return {
            "risk_score":    round(prob, 4),
            "triage_level":  triage,
            "top_factors":   top_factors,
            "recommendation": self._recommendation(triage),
        }

    def _triage_level(self, prob: float) -> str:
        if prob >= TRIAGE_THRESHOLDS["High"]:
            return "High"
        if prob >= TRIAGE_THRESHOLDS["Medium"]:
            return "Medium"
        return "Low"

    def _top_factors(self, features: np.ndarray, top_n: int = 4) -> list[dict]:
        base_model = self.model.estimator if hasattr(self.model, "estimator") else self.model.calibrated_classifiers_[0].estimator
        importances = base_model.feature_importances_
        weighted = features * importances
        ranked_idx = np.argsort(weighted)[::-1][:top_n]
        return [
            {"feature": FEATURE_NAMES[i], "value": round(float(features[i]), 3), "importance": round(float(importances[i]), 3)}
            for i in ranked_idx
            if features[i] > 0
        ]

    def _recommendation(self, triage: str) -> str:
        return {
            "High":   "Immediate psychiatric evaluation. Consider inpatient admission.",
            "Medium": "Urgent outpatient follow-up within 48 hours.",
            "Low":    "Routine outpatient care. Monitor for symptom escalation.",
        }[triage]


if __name__ == "__main__":
    scorer = RiskScorer()

    note = """
    32-year-old female presents with severe depressive episode, suicidal ideation,
    PHQ-9 score of 22, GAF score 35. History of Bipolar I Disorder.
    Currently prescribed Quetiapine and Lithium. Reports recent psychotic symptoms.
    """

    mock_graphrag = {
        "full_context": "Patient has severe episode. Diagnosis: Bipolar I Disorder.",
        "total_queries": 6,
        "successful_queries": 5,
    }

    result = scorer.score(note, mock_graphrag)
    print(f"\nRisk Score:    {result['risk_score']}")
    print(f"Triage Level:  {result['triage_level']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Top Factors:")
    for f in result["top_factors"]:
        print(f"  {f['feature']}: value={f['value']}, importance={f['importance']}")