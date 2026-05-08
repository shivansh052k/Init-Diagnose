"""
Deploy XGBoost risk scorer to AWS SageMaker.

Prerequisites:
    pip install boto3 sagemaker
    AWS credentials configured (~/.aws/credentials)
    S3 bucket created for model artifacts

Usage:
    python serving/sagemaker_deploy.py --bucket your-s3-bucket --role arn:aws:iam::...

DO NOT RUN without AWS credentials + budget — endpoint costs ~$0.10/hr (ml.t2.medium).
"""
import argparse
import tarfile
import boto3
import sagemaker
from pathlib import Path
from sagemaker.xgboost import XGBoostModel

ARTIFACTS_DIR = Path("serving/triton_model_repo/risk_scorer/model_artifacts")
MODEL_TAR     = Path("serving/model.tar.gz")
ENTRY_POINT   = Path("serving/sagemaker_inference.py")
SM_FRAMEWORK  = "1.7-1"   # SageMaker XGBoost framework version


def _write_inference_script():
    """SageMaker entry point script — inline for self-containment."""
    script = '''
import os
import json
import numpy as np
from xgboost import XGBClassifier

def model_fn(model_dir):
    model = XGBClassifier()
    model.load_model(os.path.join(model_dir, "xgb_model.json"))
    cal = np.load(os.path.join(model_dir, "calibration_params.npy"))
    return {"model": model, "cal_a": float(cal[0]), "cal_b": float(cal[1])}

def input_fn(request_body, content_type="application/json"):
    data = json.loads(request_body)
    return np.array(data["features"], dtype=np.float32).reshape(-1, 16)

def predict_fn(X, model_dict):
    raw = model_dict["model"].predict(X, output_margin=True)
    a, b = model_dict["cal_a"], model_dict["cal_b"]
    prob = 1.0 / (1.0 + np.exp(a * raw + b))
    return prob.tolist()

def output_fn(prediction, accept="application/json"):
    return json.dumps({"risk_scores": prediction}), "application/json"
'''
    ENTRY_POINT.write_text(script.strip())
    print(f"Inference script → {ENTRY_POINT}")


def _package_model():
    with tarfile.open(MODEL_TAR, "w:gz") as tar:
        tar.add(ARTIFACTS_DIR / "xgb_model.json",          arcname="xgb_model.json")
        tar.add(ARTIFACTS_DIR / "calibration_params.npy",  arcname="calibration_params.npy")
    print(f"Model tarball → {MODEL_TAR}")


def deploy(bucket: str, role_arn: str, instance_type: str = "ml.t2.medium"):
    _write_inference_script()
    _package_model()

    session = sagemaker.Session(boto_session=boto3.Session())

    print(f"Uploading model to s3://{bucket}/risk-scorer/model.tar.gz ...")
    s3_uri = session.upload_data(
        path=str(MODEL_TAR),
        bucket=bucket,
        key_prefix="risk-scorer",
    )
    print(f"S3 URI: {s3_uri}")

    model = XGBoostModel(
        model_data=s3_uri,
        role=role_arn,
        entry_point=str(ENTRY_POINT),
        framework_version=SM_FRAMEWORK,
        sagemaker_session=session,
    )

    print(f"Deploying to {instance_type} ...")
    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=instance_type,
    )

    print(f"\nEndpoint name: {predictor.endpoint_name}")
    print("Test call:")
    result = predictor.predict({"features": [[0.4, 1.0, 0.0, 0.4, 0.0, 0.0, 1.0, 1.0, 0.0, 0.8, 0.7, 0.6, 0.4, 1.0, 1.0, 0.5]]})
    print(f"  Response: {result}")

    print("\nTo delete endpoint (stop billing):")
    print(f"  predictor.delete_endpoint()")
    return predictor


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--role",   required=True)
    parser.add_argument("--instance", default="ml.t2.medium")
    args = parser.parse_args()
    deploy(args.bucket, args.role, args.instance)