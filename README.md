
## Run the Airflow pipeline locally (Milestone 3)
This repo includes an Airflow DAG at `dags/train_pipeline.py` with three tasks:
`preprocess_data -> train_model -> register_model`.

### Setup
```bash
python3 -m venv .venv-m3
source .venv-m3/bin/activate
pip install --upgrade pip

AIRFLOW_VERSION=2.9.3
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

pip install -r requirements.txt

