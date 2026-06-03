from __future__ import annotations

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from phishguard.detector import train_model


if __name__ == "__main__":
    metrics = train_model(
        dataset_path=BASE_DIR / "data" / "sample_emails.csv",
        model_path=BASE_DIR / "artifacts" / "phishing_detector.joblib",
    )
    print(metrics)
