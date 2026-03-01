"""
Milestone 3 - Training script

Requirements (checklist):
- MUST be a Python script (not a notebook)
- Logs params, metrics, and artifacts to MLflow
- Produces a saved model artifact for later registration
"""

from __future__ import annotations

import argparse
import json
import hashlib
import os
from pathlib import Path

import mlflow
import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib



def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--experiment-name", default="milestone3")
    p.add_argument("--run-name", default=None)
    p.add_argument("--C", type=float, default=1.0)
    p.add_argument("--max-iter", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output-dir", default="artifacts")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Simple, deterministic dataset for now (we can swap to your real dataset later)
    X, y = load_iris(return_X_y=True)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=args.seed, stratify=y
    )

    model = LogisticRegression(C=args.C, max_iter=args.max_iter, n_jobs=None)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)
    acc = float(accuracy_score(y_val, preds))

    # Save model artifact
    model_path = out_dir / "model.joblib"
    joblib.dump(model, model_path)

    # Save a small metadata artifact
    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps({"accuracy": acc}, indent=2))

    # Compute artifact hashes for reproducibility
    model_sha256 = sha256_file(model_path)
    metrics_sha256 = sha256_file(metrics_path)

    # MLflow logging
    mlflow.set_experiment(args.experiment_name)
    with mlflow.start_run(run_name=args.run_name):
        mlflow.log_param("C", args.C)
        mlflow.log_param("max_iter", args.max_iter)
        mlflow.log_param("seed", args.seed)

        mlflow.log_metric("val_accuracy", acc)

        mlflow.log_artifact(str(model_path))
        mlflow.log_artifact(str(metrics_path))

        # Log artifact hashes as tags (checklist requirement)
        mlflow.set_tag("artifact_sha256_model_joblib", model_sha256)
        mlflow.set_tag("artifact_sha256_metrics_json", metrics_sha256)

        # Print key outputs for Airflow/CI logs
        print(f"val_accuracy={acc}")
        print(f"model_path={model_path.resolve()}")


if __name__ == "__main__":
    main()
