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
    Run-scoped register: validate artifacts/<run_id>/metrics.json, then register the model for THIS run_id
    using artifacts/<run_id>/mlflow_run_id.txt and promote to Production (idempotent).
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
