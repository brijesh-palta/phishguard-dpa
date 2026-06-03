# AI-Powered Phishing Detection and Simulation Platform

Python + GoPhish MVP for phishing email detection, simulation tracking, and gamified employee risk scoring.

## Quick Start
```powershell
python scripts\train_model.py
python -m uvicorn app:app --reload --port 8000
```

Open:
```text
http://127.0.0.1:8000
```

## What Is Included
- Python phishing detector using TF-IDF, URL heuristics, and Logistic Regression.
- Sender trust checks for company domain match, free email providers, reply-to mismatch, lookalike domains, and suspicious TLDs.
- HTML email analysis for disguised links, hidden content, forms, scripts, tracking images, remote images, and risky attachment names.
- FastAPI backend with detection, metrics, event tracking, and challenge generation APIs.
- Browser dashboard for email analysis, campaign metrics, leaderboard, event simulation, and rendered training email previews.
- Safe training challenge generator that returns plain text, HTML, local training links, image assets, and a GoPhish-ready template payload.
- GoPhish setup guide for local authorized awareness campaigns.
- Unit tests for detection and risk scoring.

## Rich Email Detection Fields
`POST /api/detect` accepts the original `subject`, `body`, and `urls` fields plus optional rich email fields:

```json
{
  "html_body": "<a href=\"http://example-work.xyz/login\">https://example.com/login</a>",
  "image_urls": ["http://example-work.xyz/open-pixel.gif"],
  "attachment_names": ["invoice.pdf.exe"]
}
```

The response includes `sender_analysis` and `structure_analysis` so the dashboard can explain whether risk came from content, sender identity, links, images, HTML, or attachments.

## Useful Commands
```powershell
python scripts\train_model.py
python -m unittest discover -s tests
python -m uvicorn app:app --reload --port 8000
```

## Training With Larger Public Datasets
Install the Parquet dependency first:
```powershell
python -m pip install -r requirements.txt
```

Recommended public source for a stronger baseline:
```powershell
python scripts\build_training_dataset.py --download-hf-seven train eval test --include-sample --output data\processed\training_emails.csv
python scripts\train_model.py --dataset data\processed\training_emails.csv --recall-floor 0.92
```

Kaggle sources can also be added after configuring your Kaggle API token:
```powershell
kaggle datasets download -d avnbluefox/avn-phishing-email-classification-dataset -p data\raw\kaggle\avn --unzip
kaggle datasets download -d naserabdullahalam/phishing-email-dataset -p data\raw\kaggle\naser --unzip
python scripts\build_training_dataset.py --include-raw-dir --include-sample --output data\processed\training_emails.csv
python scripts\train_model.py --dataset data\processed\training_emails.csv --recall-floor 0.92
```

Raw public corpora can contain personal data and malicious URLs. Keep `data/raw`, `data/processed`, and `artifacts` local and do not click links found inside training data.

## Project Documents
- `docs/15_day_plan.md`
- `docs/gophish_setup.md`
- `docs/security_scope.md`
- `docs/training_data_sources.md`
