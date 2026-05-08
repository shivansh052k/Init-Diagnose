"""
Triton Python backend inference script for risk_scorer.
Loads XGBoost + Platt calibration params on startup.
Runs inference on each request batch.
"""
import json
import numpy as np
import triton_python_backend_utils as pb_utils
from xgboost import XGBClassifier
from pathlib import Path


ARTIFACTS_DIR = Path(__file__).parent.parent / "model_artifacts"


def _sigmoid(x, a, b):
    return 1.0 / (1.0 + np.exp(a * x + b))


class TritonPythonModel:

    def initialize(self, args):
        model_json = str(ARTIFACTS_DIR / "xgb_model.json")
        cal_path   = str(ARTIFACTS_DIR / "calibration_params.npy")

        self.xgb = XGBClassifier()
        self.xgb.load_model(model_json)

        cal = np.load(cal_path)
        self.cal_a = float(cal[0])
        self.cal_b = float(cal[1])

    def execute(self, requests):
        responses = []

        for request in requests:
            features = pb_utils.get_input_tensor_by_name(request, "features")
            X = features.as_numpy().astype(np.float32)          # shape: (batch, 16)

            raw_scores = self.xgb.predict(X, output_margin=True) # decision values
            calibrated = _sigmoid(raw_scores, self.cal_a, self.cal_b).astype(np.float32)

            out_tensor = pb_utils.Tensor(
                "risk_score",
                calibrated.reshape(-1, 1),
            )
            responses.append(pb_utils.InferenceResponse([out_tensor]))

        return responses

    def finalize(self):
        pass