import sys
import numpy as np
import matplotlib.pyplot as plt
import joblib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, roc_curve,
    average_precision_score, precision_recall_curve,
    classification_report, brier_score_loss,
)
from sklearn.calibration import calibration_curve

from risk_scorer.feature_extractor import FEATURE_NAMES

DATA_PATH  = "data/risk_train.npz"
MODEL_PATH = Path("risk_scorer/model/xgb_calibrated.pkl")
PLOTS_DIR  = Path("risk_scorer/plots")


def evaluate():
    print("Loading data and model...")
    d = np.load(DATA_PATH)
    X, y = d["X"], d["y"]
    model = joblib.load(MODEL_PATH)

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    auroc = roc_auc_score(y_test, probs)
    auprc = average_precision_score(y_test, probs)
    brier = brier_score_loss(y_test, probs)

    print(f"\n── Evaluation Report ────────────────────────────")
    print(f"  AUROC : {auroc:.4f}")
    print(f"  AUPRC : {auprc:.4f}")
    print(f"  Brier : {brier:.4f}")
    print(f"\n{classification_report(y_test, preds, target_names=['Low-Risk', 'High-Risk'])}")

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    _plot_roc(y_test, probs, auroc)
    _plot_pr(y_test, probs, auprc)
    _plot_calibration(y_test, probs)
    _plot_feature_importance(model)
    print(f"\nPlots saved → {PLOTS_DIR}/")


def _plot_roc(y_test, probs, auroc):
    fpr, tpr, _ = roc_curve(y_test, probs)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, lw=2, label=f"XGBoost (AUROC={auroc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=1)
    plt.axvline(x=0.1, color="gray", linestyle=":", alpha=0.5)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve — Risk Scorer")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "roc_curve.png", dpi=150)
    plt.close()


def _plot_pr(y_test, probs, auprc):
    precision, recall, _ = precision_recall_curve(y_test, probs)
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, lw=2, label=f"XGBoost (AUPRC={auprc:.3f})")
    baseline = y_test.mean()
    plt.axhline(y=baseline, color="k", linestyle="--", lw=1, label=f"Baseline ({baseline:.2f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve — Risk Scorer")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "pr_curve.png", dpi=150)
    plt.close()


def _plot_calibration(y_test, probs):
    fraction_pos, mean_pred = calibration_curve(y_test, probs, n_bins=10)
    plt.figure(figsize=(6, 5))
    plt.plot(mean_pred, fraction_pos, "s-", label="XGBoost (calibrated)")
    plt.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
    plt.xlabel("Mean Predicted Probability")
    plt.ylabel("Fraction of Positives")
    plt.title("Calibration Curve — Risk Scorer")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "calibration_curve.png", dpi=150)
    plt.close()


def _plot_feature_importance(model):
    base = model.calibrated_classifiers_[0].estimator
    importances = base.feature_importances_
    idx = np.argsort(importances)
    plt.figure(figsize=(7, 6))
    plt.barh([FEATURE_NAMES[i] for i in idx], importances[idx], color="steelblue")
    plt.xlabel("Feature Importance (gain)")
    plt.title("XGBoost Feature Importance")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "feature_importance.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    evaluate()