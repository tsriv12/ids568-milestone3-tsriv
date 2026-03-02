"""
Milestone 3 - Model validation (quality gate)

Used by:
- GitHub Actions: fail the workflow if model does not meet threshold
- Airflow (optional): can be called after training

Contract:
- Reads metrics from artifacts/metrics.json by default
- Exits non-zero if validation fails
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--metrics-path", default="artifacts/metrics.json")
    p.add_argument("--min-accuracy", type=float, default=0.80)
    p.add_argument("--baseline-metrics", default=None)
    p.add_argument("--max-regression", type=float, default=0.0)
    return p.parse_args()


def main():
    args = parse_args()
    metrics_path = Path(args.metrics_path)

    if not metrics_path.exists():
        print(f"ERROR: metrics file not found: {metrics_path}", file=sys.stderr)
        return 2

    metrics = json.loads(metrics_path.read_text())
    acc = float(metrics.get("accuracy", float("nan")))

    if acc != acc:  # NaN check
        print("ERROR: accuracy missing/NaN in metrics.json", file=sys.stderr)
        return 3



    # Regression gate vs baseline (optional)
    if args.baseline_metrics:
        baseline_path = Path(args.baseline_metrics)
        if not baseline_path.exists():
            print(f"ERROR: baseline metrics file not found: {baseline_path}", file=sys.stderr)
            return 4
        baseline = json.loads(baseline_path.read_text())
        base_acc = float(baseline.get("val_accuracy", float("nan")))
        if base_acc != base_acc:
            print("ERROR: val_accuracy missing/NaN in baseline metrics", file=sys.stderr)
            return 5
        print(f"baseline: val_accuracy={base_acc} (max_regression={args.max_regression})")
        if acc < base_acc - args.max_regression:
            print("FAIL: metric regression vs baseline", file=sys.stderr)
            return 11
 

    print(f"validation: accuracy={acc} (min={args.min_accuracy})")
    if acc < args.min_accuracy:
        print("FAIL: model accuracy below threshold", file=sys.stderr)
        return 10

    print("PASS: model meets threshold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
