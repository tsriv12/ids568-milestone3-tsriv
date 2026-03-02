# Milestone 3 — Evidence Checklist (Screenshots)

## MLflow Tracking (screenshots)
1) **Experiment runs**
   - Open MLflow UI → experiment `milestone3`
   - Screenshot showing **>= 5 runs** and the `val_accuracy` metric column visible.

2) **Run details (artifact hashing)**
   - Open the best run used for registry promotion
   - Screenshot of:
     - params (`C`, `max_iter`, `seed`)
     - metrics (`val_accuracy`)
     - tags showing:
       - `artifact_sha256_model_joblib`
       - `artifact_sha256_metrics_json`

3) **Model Registry**
   - MLflow UI → Models → `milestone3_model`
   - Screenshot showing:
     - Version 1 in **Production**
     - Stage history (None → Staging → Production)
     - Tags (e.g., `stage_promotion`, `selection_criterion`, `quality_gate`)

## Airflow DAG (screenshots or CLI output)
4) **DAG success**
   - Screenshot or CLI output of:
     `airflow tasks states-for-dag-run train_pipeline <RUN_ID>`
   - Must show all 3 tasks: `preprocess_data`, `train_model`, `register_model` = **success**

## CI/CD (GitHub Actions)
5) **Workflow pass**
   - GitHub Actions → latest `Train and Validate` run
   - Screenshot showing **green** status and the log lines:
     - `val_accuracy=...`
     - `PASS: model meets threshold`

