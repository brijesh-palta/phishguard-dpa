from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from phishguard.detector import FEATURE_COLUMNS


HF_SEVEN_DATASET = {
    "train": "https://huggingface.co/datasets/puyang2025/seven-phishing-email-datasets/resolve/main/train.parquet",
    "eval": "https://huggingface.co/datasets/puyang2025/seven-phishing-email-datasets/resolve/main/eval.parquet",
    "test": "https://huggingface.co/datasets/puyang2025/seven-phishing-email-datasets/resolve/main/test.parquet",
}

COLUMN_ALIASES = {
    "subject": ["subject", "Subject", "email_subject", "Email Subject", "title"],
    "body": ["body", "Body", "text", "Text", "message", "Message", "email", "Email Text", "content"],
    "urls": ["urls", "url", "URL", "links", "Links", "num_urls", "url_count"],
    "html_body": ["html_body", "html", "HTML", "html_content"],
    "image_urls": ["image_urls", "images", "image", "img_urls"],
    "attachment_names": ["attachment_names", "attachments", "attachment", "files"],
    "sender_email": ["sender_email", "sender", "from", "From", "Sender"],
    "reply_to_email": ["reply_to_email", "reply_to", "Reply-To", "reply-to"],
    "expected_domain": ["expected_domain", "company_domain", "organization_domain"],
    "label": ["label", "Label", "class", "Class", "target", "Target", "spam", "phishing"],
    "source_dataset": ["dataset_name", "source", "Source", "source_dataset"],
}

PHISHING_LABELS = {"1", "phishing", "phish", "spam", "scam", "malicious", "bad", "true", "yes"}
LEGITIMATE_LABELS = {"0", "legitimate", "legit", "ham", "safe", "benign", "good", "false", "no"}
DROP_LABELS = {"2", "garbage", "noise", "unknown", "nan", ""}


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    by_lower = {column.lower(): column for column in columns}
    for alias in aliases:
        if alias in columns:
            return alias
        if alias.lower() in by_lower:
            return by_lower[alias.lower()]
    return None


def _map_label(value: object) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text.endswith(".0"):
        text = text[:-2]
    if text in PHISHING_LABELS:
        return 1
    if text in LEGITIMATE_LABELS:
        return 0
    if text in DROP_LABELS:
        return None
    return None


def _looks_numeric(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series.dropna().astype(str).str.strip(), errors="coerce")
    return not numeric.empty and numeric.notna().mean() >= 0.9


def _as_text_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series([""] * len(frame), index=frame.index, dtype="string")
    return frame[column].fillna("").astype(str)


def normalize_dataframe(frame: pd.DataFrame, source_name: str = "unknown", min_body_chars: int = 20) -> pd.DataFrame:
    columns = list(frame.columns)
    resolved = {name: _find_column(columns, aliases) for name, aliases in COLUMN_ALIASES.items()}
    label_column = resolved["label"]
    if label_column is None:
        raise ValueError(f"{source_name} does not contain a recognizable label column")

    normalized = pd.DataFrame(index=frame.index)
    normalized["subject"] = _as_text_series(frame, resolved["subject"])
    normalized["body"] = _as_text_series(frame, resolved["body"])

    urls_column = resolved["urls"]
    if urls_column and _looks_numeric(frame[urls_column]):
        normalized["urls"] = ""
        normalized["url_count_hint"] = pd.to_numeric(frame[urls_column], errors="coerce").fillna(0).clip(lower=0)
    else:
        normalized["urls"] = _as_text_series(frame, urls_column)
        normalized["url_count_hint"] = normalized["urls"].str.len().gt(0).astype(int)

    for column in [
        "html_body",
        "image_urls",
        "attachment_names",
        "sender_email",
        "reply_to_email",
        "expected_domain",
    ]:
        normalized[column] = _as_text_series(frame, resolved[column])

    source_column = resolved["source_dataset"]
    normalized["source_dataset"] = _as_text_series(frame, source_column) if source_column else source_name
    normalized["label"] = frame[label_column].map(_map_label)
    normalized = normalized.dropna(subset=["label"]).copy()
    normalized["label"] = normalized["label"].astype(int)
    normalized["body"] = normalized["body"].str.replace(r"\s+", " ", regex=True).str.strip()
    normalized["subject"] = normalized["subject"].str.replace(r"\s+", " ", regex=True).str.strip()
    normalized = normalized[
        (normalized["subject"].str.len() + normalized["body"].str.len()) >= min_body_chars
    ].copy()
    normalized = normalized.drop_duplicates(
        subset=["subject", "body", "sender_email", "label"],
        keep="first",
    )
    return normalized[[*FEATURE_COLUMNS, "label", "source_dataset"]]


def read_source(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    if path.suffix.lower() in {".csv", ".txt"}:
        return pd.read_csv(path, low_memory=False)
    raise ValueError(f"Unsupported dataset file type: {path}")


def download_file(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        return destination
    with urlopen(url) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return destination


def discover_local_sources(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in {".csv", ".txt", ".parquet"}
    )


def balance_frame(frame: pd.DataFrame, max_per_class: int | None, random_state: int) -> pd.DataFrame:
    if not max_per_class:
        return frame
    pieces = []
    for _, group in frame.groupby("label"):
        pieces.append(group.sample(n=min(len(group), max_per_class), random_state=random_state))
    return pd.concat(pieces, ignore_index=True).sample(frac=1, random_state=random_state)


def build_dataset(args: argparse.Namespace) -> dict:
    raw_dir = BASE_DIR / "data" / "raw"
    sources = [Path(path) for path in args.source]

    for split in args.download_hf_seven:
        url = HF_SEVEN_DATASET[split]
        destination = raw_dir / "hf-seven-phishing-email-datasets" / f"{split}.parquet"
        sources.append(download_file(url, destination))

    if args.include_raw_dir:
        sources.extend(discover_local_sources(raw_dir))

    if args.include_sample:
        sources.append(BASE_DIR / "data" / "sample_emails.csv")

    sources = sorted(set(path.resolve() for path in sources if path.exists()))
    if not sources:
        raise ValueError("No dataset sources were found")

    normalized_frames = []
    source_stats = []
    for source in sources:
        frame = read_source(source)
        normalized = normalize_dataframe(frame, source_name=source.stem, min_body_chars=args.min_body_chars)
        normalized_frames.append(normalized)
        source_stats.append(
            {
                "source": str(source),
                "input_rows": int(len(frame)),
                "usable_rows": int(len(normalized)),
                "class_counts": normalized["label"].value_counts().to_dict(),
            }
        )

    combined = pd.concat(normalized_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["subject", "body", "sender_email", "label"], keep="first")
    combined = balance_frame(combined, args.max_per_class, args.random_state)
    combined = combined.sample(frac=1, random_state=args.random_state).reset_index(drop=True)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output, index=False)

    return {
        "output": str(output),
        "rows": int(len(combined)),
        "class_counts": {str(key): int(value) for key, value in combined["label"].value_counts().to_dict().items()},
        "sources": source_stats,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normalized phishing email training dataset.")
    parser.add_argument("--source", action="append", default=[], help="CSV/TXT/Parquet dataset path. Can be repeated.")
    parser.add_argument(
        "--download-hf-seven",
        nargs="*",
        choices=sorted(HF_SEVEN_DATASET),
        default=[],
        help="Download public Hugging Face seven-dataset Parquet split(s). Example: --download-hf-seven train eval",
    )
    parser.add_argument("--include-raw-dir", action="store_true", help="Include all CSV/TXT/Parquet files under data/raw.")
    parser.add_argument("--include-sample", action="store_true", help="Include data/sample_emails.csv.")
    parser.add_argument("--output", default=str(BASE_DIR / "data" / "processed" / "training_emails.csv"))
    parser.add_argument("--max-per-class", type=int, default=None, help="Optional cap per class for balanced quick training.")
    parser.add_argument("--min-body-chars", type=int, default=20)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    stats = build_dataset(parse_args())
    print(stats)
