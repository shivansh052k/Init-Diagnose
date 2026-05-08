import sys
import numpy as np
import joblib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from xgboost import XGBClassifier

from risk_scorer.data_generator import RiskDataGenerator
from risk_scorer.feature_extractor import FEATURE_NAMES

DATA_PATH = "data/risk_train.npz"
MODEL_DIR = Path("risk_scorer/model")
MODEL_PATH = MODEL_DIR / "xgb_calibrated.pkl"


def load_or_generate() -> tuple[np.ndarray, np.ndarray]:
    if Path(DATA_PATH).exists():
        print(f"Loading cached data from {DATA_PATH}")
        d = np.load(DATA_PATH)
        return d["X"], d["y"]
    print("No cached data — generating from Neo4j...")
    gen = RiskDataGenerator()
    try:
        return gen.generate(n_patients=5000, save_path=DATA_PATH)
    finally:
        gen.close()


def train():
    X, y = load_or_generate()
    print(f"\nDataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"Class balance: {y.mean():.1%} high-risk\n")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42, stratify=y_train
    )

    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    base = XGBClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        early_stopping_rounds=30,
        random_state=42,
        verbosity=0,
    )

    base.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    best_iter = base.best_iteration
    print(f"Best iteration: {best_iter}")

    print("Calibrating with Platt scaling...")
    calibrated = CalibratedClassifierCV(base, cv="prefit", method="sigmoid")
    calibrated.fit(X_val, y_val)

    probs = calibrated.predict_proba(X_test)[:, 1]
    auroc = roc_auc_score(y_test, probs)
    auprc = average_precision_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)

    print(f"\n── Test Metrics ─────────────────")
    print(f"  AUROC : {auroc:.4f}  (target ≥ 0.86)")
    print(f"  AUPRC : {auprc:.4f}")
    print(f"  Brier : {brier:.4f}  (lower = better)")

    print(f"\nTop features by importance:")
    importances = base.feature_importances_
    ranked = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])
    for name, imp in ranked[:8]:
        bar = "█" * int(imp * 40)
        print(f"  {name:<35} {bar} {imp:.3f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibrated, MODEL_PATH)
    print(f"\nModel saved → {MODEL_PATH}")
    return auroc


if __name__ == "__main__":
    train()