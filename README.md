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
python model_validation.py --metrics-path artifacts/metrics.json --min-accuracy 0.80
