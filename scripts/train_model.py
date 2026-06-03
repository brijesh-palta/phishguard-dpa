from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from phishguard.detector import train_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the phishing email detector.")
    parser.add_argument("--dataset", default=str(BASE_DIR / "data" / "sample_emails.csv"))
    parser.add_argument("--model", default=str(BASE_DIR / "artifacts" / "phishing_detector.joblib"))
    parser.add_argument("--metrics", default=str(BASE_DIR / "artifacts" / "phishing_detector_metrics.json"))
    parser.add_argument("--test-size", type=float, default=0.25)
    parser.add_argument(
        "--recall-floor",
        type=float,
        default=0.9,
        help="Prefer a decision threshold with at least this phishing recall when possible.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    metrics = train_model(
        dataset_path=Path(args.dataset),
        model_path=Path(args.model),
        test_size=args.test_size,
        recall_floor=args.recall_floor,
    )
    metrics_path = Path(args.metrics)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
