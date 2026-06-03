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
- FastAPI backend with detection, metrics, event tracking, and challenge generation APIs.
- Browser dashboard for email analysis, campaign metrics, leaderboard, and event simulation.
- GoPhish setup guide for local authorized awareness campaigns.
- Unit tests for detection and risk scoring.

## Useful Commands
```powershell
python scripts\train_model.py
python -m unittest discover -s tests
python -m uvicorn app:app --reload --port 8000
```

## Project Documents
- `docs/15_day_plan.md`
- `docs/gophish_setup.md`
- `docs/security_scope.md`
