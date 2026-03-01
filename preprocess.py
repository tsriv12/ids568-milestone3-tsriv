"""
Optional preprocessing script (Milestone 3)

Purpose:
- Provide a standalone preprocessing step that is idempotent.
- Writes minimal metadata output into the run-specific output directory.

Usage:
  python preprocess.py --output-dir artifacts/<run_id>
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sklearn.datasets import load_iris


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", default="artifacts/preprocess")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Example: "preprocess" by loading the dataset and writing metadata
    X, y = load_iris(return_X_y=True)

    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "sklearn.datasets.load_iris",
        "n_rows": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "n_classes": int(len(set(y.tolist()))),
    }

    meta_path = out_dir / "preprocess_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    print(f"preprocess_meta_path={meta_path.resolve()}")


if __name__ == "__main__":
    main()
