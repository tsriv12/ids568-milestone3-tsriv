from __future__ import annotations

from datetime import datetime, timedelta
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator


def on_failure_callback(context):
    """
    Called when any task fails.
    Keep it simple for grading: log task + dag + execution timestamp.
    """
    ti = context.get("task_instance")
    logging.error(
        "TASK FAILED | dag=%s task=%s run_id=%s",
        context.get("dag").dag_id if context.get("dag") else None,
        ti.task_id if ti else None,
        context.get("run_id"),
    )


def preprocess_data(**kwargs):
    # TODO: implement in Step 7+
    logging.info("preprocess_data: placeholder")


def train_model(**kwargs):
    # TODO: implement in Step 7+
    logging.info("train_model: placeholder")


def register_model(**kwargs):
    # TODO: implement in Step 7+
    logging.info("register_model: placeholder")


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

    t1 = PythonOperator(
        task_id="preprocess_data",
        python_callable=preprocess_data,
    )

    t2 = PythonOperator(
        task_id="train_model",
        python_callable=train_model,
    )

    t3 = PythonOperator(
        task_id="register_model",
        python_callable=register_model,
    )

    t1 >> t2 >> t3
