from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from phishguard.detector import (
    PhishingDetectorService,
    analyze_file_content,
    analyze_sender,
)
from phishguard.generator import generate_training_challenge
from phishguard.gophish_client import get_gophish_status
from phishguard.schemas import DetectionRequest, EventRequest, TrainingRequest
from phishguard.storage import JsonStore


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

_PROCESSED_DATASET = BASE_DIR / "data" / "processed" / "training_emails.csv"
_SAMPLE_DATASET = BASE_DIR / "data" / "sample_emails.csv"
_DATASET_PATH = _PROCESSED_DATASET if _PROCESSED_DATASET.exists() else _SAMPLE_DATASET

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
    dataset_path=_DATASET_PATH,
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
        html_body=payload.html_body,
        image_urls=payload.image_urls,
        attachment_names=payload.attachment_names,
    )
    record = store.add_detection(
        {
            "subject": payload.subject,
            "body": payload.body,
            "urls": payload.urls,
            "html_body": payload.html_body,
            "image_urls": payload.image_urls,
            "attachment_names": payload.attachment_names,
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
        company_name=payload.company_name,
        base_url=payload.base_url,
    )


@app.get("/training/track/{tracking_id}")
def training_track(tracking_id: int, scenario: str = "general") -> HTMLResponse:
    safe_scenario = escape(scenario.replace("_", " ").title())
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Security Awareness Drill</title>
            <style>
              body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #eef3f8; color: #17212b; }}
              main {{ max-width: 760px; margin: 48px auto; padding: 28px; background: #ffffff; border: 1px solid #d9e2ec; border-radius: 8px; }}
              h1 {{ margin: 0 0 12px; font-size: 28px; }}
              p {{ line-height: 1.55; }}
              .pill {{ display: inline-block; padding: 6px 10px; border-radius: 999px; background: #e8f2ff; color: #2368d1; font-weight: 700; font-size: 12px; }}
            </style>
          </head>
          <body>
            <main>
              <div class="pill">Authorized training</div>
              <h1>Security Awareness Drill</h1>
              <p>You opened a safe training link for the <strong>{safe_scenario}</strong> scenario.</p>
              <p>In a real review, inspect the sender, hover over links, check domains, and report suspicious messages through your approved process.</p>
              <p>Tracking ID: {tracking_id}</p>
            </main>
          </body>
        </html>
        """
    )


@app.get("/training/tips")
def training_tips(scenario: str = "general") -> HTMLResponse:
    safe_scenario = escape(scenario.replace("_", " ").title())
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Phishing Safety Tips</title>
            <style>
              body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #eef3f8; color: #17212b; }}
              main {{ max-width: 760px; margin: 48px auto; padding: 28px; background: #ffffff; border: 1px solid #d9e2ec; border-radius: 8px; }}
              h1 {{ margin: 0 0 12px; font-size: 28px; }}
              li {{ margin: 10px 0; line-height: 1.45; }}
            </style>
          </head>
          <body>
            <main>
              <h1>{safe_scenario} Safety Tips</h1>
              <ul>
                <li>Check whether the sender domain matches the expected organization.</li>
                <li>Hover over buttons and links before opening them.</li>
                <li>Be cautious with forms, hidden content, tracking images, and unexpected attachments.</li>
                <li>Report suspicious emails through the approved company channel.</li>
              </ul>
            </main>
          </body>
        </html>
        """
    )


_ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".eml",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif",
}
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@app.post("/api/detect/upload")
async def detect_uploaded_file(
    file: UploadFile = File(...),
    sender_email: str = Form(default=""),
    expected_domain: str = Form(default=""),
) -> JSONResponse:
    filename = file.filename or "unknown"
    suffix = Path(filename.lower()).suffix
    if suffix not in _ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(_ALLOWED_UPLOAD_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    file_analysis = analyze_file_content(filename, content)

    sender_result = None
    if sender_email:
        sender_result = analyze_sender(sender_email, expected_domain=expected_domain)

    risk_score = file_analysis.get("risk_score", 0)
    if sender_result:
        risk_score = max(risk_score, sender_result.get("risk_score", 0))

    label = "phishing" if risk_score >= 50 else "legitimate"
    risk_level = "high" if risk_score >= 75 else "medium" if risk_score >= 40 else "low"

    return JSONResponse({
        "filename": filename,
        "file_type": file_analysis.get("type", "unknown"),
        "label": label,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "file_analysis": file_analysis,
        "sender_analysis": sender_result,
    })


@app.get("/api/gophish/status")
def gophish_status() -> dict:
    return get_gophish_status()
