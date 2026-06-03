# 15-Day Delivery Plan

## Goal
Build an industry-style MVP for an AI-powered phishing detection and simulation platform using Python and GoPhish.

## Day-by-Day Roadmap
| Day | Focus | Output |
| --- | --- | --- |
| 1 | Project setup | Repository structure, environment, first FastAPI app, sample data |
| 2 | Dataset and baseline model | Clean phishing/legitimate email dataset, TF-IDF + Logistic Regression model |
| 3 | Feature engineering | URL features, suspicious keyword features, model explanation output |
| 4 | Detection API | `/api/detect`, detection logs, confidence and risk level |
| 5 | Detection dashboard | Email analyzer UI, results view, recent detections |
| 6 | GoPhish setup | Local GoPhish runbook, test template, safe landing page |
| 7 | Campaign workflow | Campaign records, target users, simulation event structure |
| 8 | Behavior tracking | Open/click/submit/report event logging |
| 9 | Gamification | Risk score formula, points, badges, leaderboard |
| 10 | Analytics | Click rate, report rate, submit rate, high-risk employees |
| 11 | GoPhish API integration | API key setup, campaign status fetch, documented limitations |
| 12 | Security controls | Input validation, role plan, safe simulation boundaries |
| 13 | Testing | Unit tests, API tests, model test results |
| 14 | Documentation | Architecture diagram, screenshots, user guide, final report draft |
| 15 | Demo polish | Run-through, presentation slides, backup screenshots/video |

## MVP Acceptance Criteria
- A user can paste an email and URL into the dashboard and receive a phishing/legitimate result.
- The model returns confidence, risk level, and explanation reasons.
- The dashboard shows campaign metrics and employee risk scores.
- Behavior events update gamification points and leaderboard ranking.
- GoPhish can be run locally and connected later with an API key.
- The project has a clear report-ready architecture and testing story.
