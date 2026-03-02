from __future__ import annotations

from datetime import datetime, timedelta
import logging
import os
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


def on_failure_callback(context):
    ti = context.get("task_instance")
    logging.error(
        "TASK FAILED | dag=%s task=%s run_id=%s",
        context.get("dag").dag_id if context.get("dag") else None,
        ti.task_id if ti else None,
        context.get("run_id"),
    )


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTIFACTS_DIR = os.path.join(REPO_ROOT, "artifacts")


def preprocess_data(**kwargs):
    """Idempotent preprocess: ensure the run-scoped artifacts directory exists."""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    logging.info("Preprocess complete. artifacts_dir=%s", ARTIFACTS_DIR)


def train_model(**kwargs):
    """
    Calls train.py. Idempotency: overwrites artifacts/ for this run.
    """
    env = os.environ.copy()
    cmd = ["python", os.path.join(REPO_ROOT, "train.py"), "--experiment-name", "milestone3", "--run-name", "airflow_run", "--output-dir", f"artifacts/{kwargs.get('run_id', 'airflow')}" ]
    logging.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True)


def register_model(**kwargs):
    env = os.environ.copy()
    env["M3_RUN_ID"] = kwargs.get("run_id", "airflow")
    """
    Runs validation gate, then registers and promotes best run to Production.
    For simplicity, we register the last run that 'train.py' created via MLflow search.
    """
    # 1) quality gate (fails task if below threshold)
    cmd_val = ["python", os.path.join(REPO_ROOT, "model_validation.py"), "--metrics-path", f"artifacts/{kwargs.get('run_id', 'airflow')}/metrics.json", "--min-accuracy", "0.80"]
    logging.info("Running: %s", " ".join(cmd_val))
    subprocess.run(cmd_val, cwd=REPO_ROOT, env=env, check=True)

    # 2) register + promote using MLflow API
    cmd_reg = [
        "python",
        "-c",
                """
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
model_name = "milestone3_model"

exp = mlflow.get_experiment_by_name("milestone3")
if exp is None:
    raise SystemExit("ERROR: MLflow experiment 'milestone3' not found")

runs = mlflow.search_runs(experiment_ids=[exp.experiment_id]).sort_values(
    "metrics.val_accuracy", ascending=False
)
if len(runs) == 0:
    raise SystemExit("ERROR: No runs found in experiment 'milestone3'")

best = runs.iloc[0]
best_run_id = best["run_id"]
model_uri = f"runs:/{best_run_id}/model.joblib"

# Ensure registered model exists
try:
    client.create_registered_model(model_name)
except Exception:
    pass

# Idempotent: if Production already points to this run_id, skip
for v in client.get_latest_versions(model_name, stages=["Production"]):
    if getattr(v, "run_id", None) == best_run_id:
        print(f"SKIP: Production already at v{v.version} for run_id={best_run_id}")
        raise SystemExit(0)

mv = mlflow.register_model(model_uri, model_name)
client.transition_model_version_stage(
    name=model_name, version=mv.version, stage="Staging", archive_existing_versions=False
)
client.transition_model_version_stage(
    name=model_name, version=mv.version, stage="Production", archive_existing_versions=False
)

print(f"Registered/promoted: {model_name} v{mv.version} from run_id={best_run_id}")
    """
    ]
    logging.info("Running MLflow register/promote")
    subprocess.run(cmd_reg, cwd=REPO_ROOT, env=env, check=True)


default_args = {
    "owner": "ids568",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "on_failure_callback": on_failure_callback,
}

with DAG(
    dag_id="train_pipeline",
    default_args=default_args,
    description="Milestone 3: preprocess -> train -> register (MLflow)",
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=["milestone3"],
) as dag:

    t1 = PythonOperator(task_id="preprocess_data", python_callable=preprocess_data)
    t2 = PythonOperator(task_id="train_model", python_callable=train_model)
    t3 = PythonOperator(task_id="register_model", python_callable=register_model)

    t1 >> t2 >> t3
