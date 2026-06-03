from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from phishguard.detector import PhishingDetectorService
from phishguard.generator import generate_training_challenge
from phishguard.gophish_client import get_gophish_status
from phishguard.schemas import DetectionRequest, EventRequest, TrainingRequest
from phishguard.storage import JsonStore


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="AI Phishing Detection and Simulation Platform",
    description="MVP backend for phishing detection, awareness simulation, and gamified risk scoring.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = JsonStore(BASE_DIR / "data" / "app_state.json")
detector = PhishingDetectorService(
    dataset_path=BASE_DIR / "data" / "sample_emails.csv",
    model_path=BASE_DIR / "artifacts" / "phishing_detector.joblib",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_ready": detector.is_ready(),
        "storage_ready": store.is_ready(),
    }


@app.post("/api/detect")
def detect_email(payload: DetectionRequest) -> dict:
    result = detector.predict(
        subject=payload.subject,
        body=payload.body,
        urls=payload.urls,
        sender_email=payload.sender_email,
        reply_to_email=payload.reply_to_email,
        expected_domain=payload.expected_domain,
    )
    record = store.add_detection(
        {
            "subject": payload.subject,
            "body": payload.body,
            "urls": payload.urls,
            "sender_email": payload.sender_email,
            "reply_to_email": payload.reply_to_email,
            "expected_domain": payload.expected_domain,
            "prediction": result,
        }
    )
    return {"id": record["id"], **result}


@app.get("/api/detections")
def list_detections() -> dict:
    return {"items": store.list_detections(limit=25)}


@app.get("/api/metrics")
def metrics() -> dict:
    return store.metrics()


@app.get("/api/employees")
def employees() -> dict:
    return {"items": store.employees_with_scores()}


@app.get("/api/campaigns")
def campaigns() -> dict:
    return {"items": store.list_campaigns()}


@app.post("/api/events")
def record_event(payload: EventRequest) -> dict:
    if payload.event_type not in {"opened", "clicked", "submitted", "reported"}:
        raise HTTPException(status_code=400, detail="Unsupported event_type")
    event = store.add_event(payload.model_dump())
    return {"event": event, "employee": store.employee_score(payload.employee_id)}


@app.post("/api/training/challenge")
def training_challenge(payload: TrainingRequest) -> dict:
    return generate_training_challenge(
        scenario=payload.scenario,
        difficulty=payload.difficulty,
        employee_name=payload.employee_name,
    )


@app.get("/api/gophish/status")
def gophish_status() -> dict:
    return get_gophish_status()
