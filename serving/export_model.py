"""
Export XGBoost model from CalibratedClassifierCV wrapper into artifacts
required by Triton FIL backend and SageMaker.

Outputs:
  serving/triton_model_repo/risk_scorer/model_artifacts/xgb_model.json
  serving/triton_model_repo/risk_scorer/model_artifacts/calibration_params.npy
"""
import sys
import numpy as np
import joblib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MODEL_PATH    = Path("risk_scorer/model/xgb_calibrated.pkl")
ARTIFACTS_DIR = Path("serving/triton_model_repo/risk_scorer/model_artifacts")


def export():
    print(f"Loading {MODEL_PATH}...")
    calibrated = joblib.load(MODEL_PATH)

    # CalibratedClassifierCV wraps one or more base estimators
    cal_clf = calibrated.calibrated_classifiers_[0]
    xgb_model = cal_clf.estimator

    # Extract Platt sigmoid calibration parameters (a, b)
    # sklearn stores them on the calibrator object
    calibrator = cal_clf.calibrators[1]  # index 1 = positive class
    a = float(calibrator.a_)
    b = float(calibrator.b_)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save XGBoost model in native JSON format (Triton FIL reads this)
    xgb_path = ARTIFACTS_DIR / "xgb_model.json"
    xgb_model.save_model(str(xgb_path))
    print(f"XGBoost model → {xgb_path}")

    # Save calibration params
    cal_path = ARTIFACTS_DIR / "calibration_params.npy"
    np.save(str(cal_path), np.array([a, b], dtype=np.float64))
    print(f"Calibration params (a={a:.4f}, b={b:.4f}) → {cal_path}")

    print("\nExport complete.")


if __name__ == "__main__":
    export()