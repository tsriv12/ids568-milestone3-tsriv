# Milestone 3 — Model Lineage Report (MLflow)

## 1) Pipeline overview
This milestone implements a 3-stage training pipeline:
1. **Preprocess**: prepare training/validation data and persist outputs deterministically.
2. **Train**: train a model with a given hyperparameter configuration and log the run to MLflow (params, metrics, artifacts).
3. **Register**: select the best candidate run and register its model artifact into the MLflow Model Registry, then promote stages.

## 2) Experiment tracking (MLflow)
All experiments were logged under the MLflow experiment: **milestone3**.

Each run logs:
- **Parameters**: `C`, `max_iter`, `seed`
- **Metric**: `val_accuracy`
- **Artifacts**: trained model (`model.joblib`) and metrics file (`metrics.json`)

A comparison table of runs is included in: `run_comparison.csv`.

## 3) Candidate selection
The production candidate was selected using:
- Selected **run_id**: `3b329cd608f94e2a904c412b8bda9d61`
- Selected **val_accuracy**: `1.0`
- Selected hyperparameters: `C=5.0`, `max_iter=200`, `seed=42`

- Primary criterion: **highest validation accuracy (`val_accuracy`)**
- Gate: validation must meet or exceed the minimum threshold enforced by `model_validation.py`

## 4) Registry actions (Model Registry)
Registered Model: **milestone3_model**

Stage progression performed for Version 1:
- **None → Staging → Production**
- Production version: **v1**

Rationale:
- The selected run achieved the best validation performance among the tracked runs and passed the validation gate.

## 5) Risks and monitoring notes
Key risks:
- **Overfitting / data shift**: validation performance may not reflect future data.
- **Reproducibility**: requires pinning dependencies and deterministic data splits.

Monitoring recommendations:
- Track serving-time metrics: accuracy proxy, drift checks, and input feature distribution shifts.
- Alert on significant drops vs baseline and rollback to a prior registry version if needed.

Rollback approach:
- Demote current Production version and promote the previous stable version in the registry.
