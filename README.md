cd /home/extramural_cl_000647/ids568-milestone3-tsriv && cat > README.md <<'MD'
# IDS568 Milestone 3

This repository implements an end-to-end MLOps workflow using **Airflow** for orchestration, **MLflow** for experiment tracking + model registry, and **GitHub Actions** for CI-based training + validation gates.

---

## Repo structure (deliverables)
- `.github/workflows/train_and_validate.yml` — CI pipeline (train + validation gate)
- `dags/train_pipeline.py` — Airflow DAG: `preprocess_data -> train_model -> register_model`
- `train.py` — training script (logs params/metrics/artifacts to MLflow; writes run-scoped artifacts)
- `model_validation.py` — validation gate (absolute threshold + regression vs baseline)
- `requirements.txt` — pinned dependencies
- `lineage_report.md` — experiment + registry lineage report
- `Evidences/`
  - `run_comparison.csv` — MLflow run comparison export
  - `baseline_metrics.json` — baseline metric used for regression gate
  - `mlflow_evidence.txt` — proof of MLflow params/metrics/tags/artifacts
  - `model_registry_evidence.txt` — proof of model version tags + description in registry

---

## What the pipeline does
1) **Train**
   - Trains a model and logs to MLflow:
     - params: `C`, `max_iter`, `seed`
     - metric: `val_accuracy`
     - artifacts: `model.joblib`, `metrics.json`
     - tags: SHA256 hashes for artifacts
2) **Validate**
   - Enforces a quality gate:
     - absolute threshold: `min_accuracy`
     - regression gate vs baseline: `baseline_metrics.json` with `max_regression`
3) **Register + Promote**
   - Registers the model produced by the **current Airflow DAG run** (run-scoped using `mlflow_run_id.txt`)
   - Adds **model version description + tags** in the MLflow Model Registry
   - Promotes the new version through **Staging → Production**
   - Safe on retries for the same DAG run (won’t re-promote the same MLflow run_id)

---

## Airflow orchestration

### DAG: `train_pipeline`
File: `dags/train_pipeline.py`

Tasks:
- `preprocess_data`  
  Ensures the artifacts directory exists.
- `train_model`  
  Executes `train.py` and writes outputs to a **run-scoped directory**:
  - `artifacts/<dag_run_id>/model.joblib`
  - `artifacts/<dag_run_id>/metrics.json`
  - `artifacts/<dag_run_id>/mlflow_run_id.txt` (MLflow run_id for that DAG run)
- `register_model`  
  1) validates `artifacts/<dag_run_id>/metrics.json` via `model_validation.py`  
  2) reads `artifacts/<dag_run_id>/mlflow_run_id.txt` to identify the MLflow run tied to this DAG run  
  3) registers `runs:/<mlflow_run_id>/model.joblib` into MLflow Model Registry  
  4) adds model version description + tags  
  5) promotes the version to **Staging** then **Production**
---

## Trigger the DAG

````bash
airflow dags trigger train_pipeline
airflow dags list-runs -d train_pipeline --no-backfill --output table | head -n 5
````
---

## CI/CD model governance (GitHub Actions)

Workflow: `.github/workflows/train_and_validate.yml`

On each push to `main`, CI:
1) Installs dependencies
2) Trains a model
3) Runs `model_validation.py` as a quality gate:
   - Must satisfy `min_accuracy`
   - Must not regress beyond `max_regression` vs `Evidences/baseline_metrics.json`

If the gate fails, CI fails.

---

## Idempotency + reproducibility

### Run-scoped artifacts
Each Airflow run writes to:
- `artifacts/<dag_run_id>/...`

This prevents different DAG runs from overwriting each other’s outputs.

### Safe on retries
`register_model` checks whether Production already points to the same MLflow `run_id` and exits early if so.  
This prevents duplicate promotions during task retries for the same DAG run.

### Artifact hashing (reproducibility)
Each training run computes SHA256 hashes and logs them as MLflow tags:
- `artifact_sha256_model_joblib`
- `artifact_sha256_metrics_json`

---

## MLflow tracking + model registry

### Experiment tracking
Experiment name: `milestone3`

Logged per run:
- Params: `C`, `max_iter`, `seed`
- Metric: `val_accuracy`
- Artifacts: `model.joblib`, `metrics.json`
- Tags: artifact SHA256 hashes

### Model registry
Registered model name: `milestone3_model`

During registration, the DAG adds:
1) Model version description (includes Airflow `dag_run_id` + MLflow `run_id`)
2) Model version tags:
   - `source_run_id`
   - `airflow_run_id`
   - `metric`
   - `gate`

---

## Monitoring / alerting recommendations
1) Monitor production performance metrics and drift indicators.
2) Alert on sustained degradation vs baseline performance.
3) Track feature distribution shifts and retrain when drift exceeds thresholds.

---

## Rollback procedure
If Production performance degrades:
1) In MLflow Model Registry, identify the last known-good Production version.
2) Promote that version back to Production (and demote/archive the current one if needed).
3) Record the rollback reason and the version/run_id selected.

---

## Update README in git

````bash
cd /home/extramural_cl_000647/ids568-milestone3-tsriv
git add README.md
git commit -m "Update README for final submission"
git push
````
