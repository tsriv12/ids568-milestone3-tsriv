# IDS568 Milestone 3

## Repo structure (expected)
- `.github/workflows/train_and_validate.yml` — CI pipeline (train + validate gate)
- `dags/train_pipeline.py` — Airflow DAG (`preprocess_data -> train_model -> register_model`)
- `train.py` — training script (logs to MLflow)
- `model_validation.py` — threshold-based validation gate
- `requirements.txt` — pinned dependencies
- `run_comparison.csv` — MLflow run comparison export
- `lineage_report.md` — experiment/registry lineage report

## Run training + validation locally (no Airflow)
```bash
python3 -m venv .venv-m3
source .venv-m3/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python train.py --experiment-name milestone3 --run-name local_run
python model_validation.py --metrics-path artifacts/local_run/metrics.json --min-accuracy 0.80
```


## Operational Notes (required checklist items)

### Architecture (how the pieces fit)
- **Airflow DAG**: `dags/train_pipeline.py` orchestrates three PythonOperator tasks.
- **Training**: `train.py` trains a model and logs params/metrics/artifacts to MLflow.
- **Validation gate**: `model_validation.py` enforces a minimum metric threshold and exits non-zero on failure.
- **Registry**: the DAG registers the best MLflow run’s model into the MLflow Model Registry and promotes it through stages.
- **CI governance**: `.github/workflows/train_and_validate.yml` runs training + validation on every push to `main`.

### Idempotency + lineage guarantees
- The DAG uses **run-scoped artifact directories**: `artifacts/<run_id>/...` so re-runs do not overwrite prior outputs.
- Each training run logs **artifact SHA256 hashes** to MLflow tags for reproducibility:
  - `artifact_sha256_model_joblib`
  - `artifact_sha256_metrics_json`
- Lineage is captured via:
  - MLflow experiment runs (params/metrics/artifacts)
  - Model Registry version history (Staging/Production transitions)
  - `run_comparison.csv` + `lineage_report.md`

### CI-based model governance approach
- PR/commit changes must pass:
  1) training execution
  2) validation threshold gate (`model_validation.py`)
- If validation fails, CI fails and blocks “good” code from landing unnoticed.

### Experiment tracking methodology
- Experiments are tracked under MLflow experiment name: `milestone3`
- Logged items:
  - Params: `C`, `max_iter`, `seed`
  - Metric: `val_accuracy`
  - Artifacts: `model.joblib`, `metrics.json`
  - Tags: SHA256 hashes for artifacts

### Retry strategy + failure handling
- Airflow `default_args` include retries + retry_delay.
- `on_failure_callback` logs the failing DAG/task/run_id for debugging.

### Monitoring/alerting recommendations
- Monitor model performance metrics in production (accuracy proxy, drift signals).
- Alert on sustained degradation vs the Production baseline.
- Track input data drift (feature distribution shifts) and retrain when drift exceeds thresholds.

### Rollback procedure
- In MLflow Model Registry:
  - Demote the current Production version (or archive it)
  - Promote the last known-good version to Production
- Document the reason for rollback and the run_id/version used.
