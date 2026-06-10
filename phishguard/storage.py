from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from phishguard.risk import campaign_metrics, score_employee


SEED_STATE = {
    "users": [
        {"id": "emp-001", "name": "Maya Rao", "email": "maya.rao@example.com", "role": "employee", "department": "HR"},
        {"id": "emp-002", "name": "Liam Chen", "email": "liam.chen@example.com", "role": "employee", "department": "Finance"},
        {"id": "emp-003", "name": "Ava Patel", "email": "ava.patel@example.com", "role": "employee", "department": "Engineering"},
        {"id": "emp-004", "name": "Noah Smith", "email": "noah.smith@example.com", "role": "employee", "department": "Sales"},
    ],
    "campaigns": [
        {
            "id": "camp-demo",
            "name": "Password Reset Awareness Drill",
            "template_type": "password_reset",
            "status": "draft",
            "target_users": ["emp-001", "emp-002", "emp-003", "emp-004"],
        }
    ],
    "events": [
        {"id": "evt-seed-1", "employee_id": "emp-001", "campaign_id": "camp-demo", "event_type": "reported", "timestamp": "2026-06-03T00:00:00+00:00"},
        {"id": "evt-seed-2", "employee_id": "emp-002", "campaign_id": "camp-demo", "event_type": "opened", "timestamp": "2026-06-03T00:02:00+00:00"},
        {"id": "evt-seed-3", "employee_id": "emp-002", "campaign_id": "camp-demo", "event_type": "clicked", "timestamp": "2026-06-03T00:03:00+00:00"},
        {"id": "evt-seed-4", "employee_id": "emp-004", "campaign_id": "camp-demo", "event_type": "opened", "timestamp": "2026-06-03T00:04:00+00:00"},
    ],
    "detections": [],
}


class JsonStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(SEED_STATE)

    def is_ready(self) -> bool:
        return self.path.exists()

    def _read(self) -> dict:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write(self, state: dict) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_detection(self, detection: dict) -> dict:
        state = self._read()
        record = {"id": f"det-{uuid4().hex[:10]}", "timestamp": self._timestamp(), **detection}
        state.setdefault("detections", []).insert(0, record)
        state["detections"] = state["detections"][:100]
        self._write(state)
        return record

    def list_detections(self, limit: int = 25) -> list[dict]:
        return self._read().get("detections", [])[:limit]

    def list_campaigns(self) -> list[dict]:
        return self._read().get("campaigns", [])

    def list_events(self, limit: int = 50, campaign_id: str | None = None, employee_id: str | None = None) -> list[dict]:
        events = self._read().get("events", [])
        if campaign_id:
            events = [event for event in events if event.get("campaign_id") == campaign_id]
        if employee_id:
            events = [event for event in events if event.get("employee_id") == employee_id]
        return events[:limit]

    def add_event(self, event: dict) -> dict:
        state = self._read()
        record = {"id": f"evt-{uuid4().hex[:10]}", "timestamp": self._timestamp(), **event}
        state.setdefault("events", []).insert(0, record)
        self._write(state)
        return record

    def employee_score(self, employee_id: str) -> dict:
        state = self._read()
        user = next((item for item in state.get("users", []) if item["id"] == employee_id), None)
        if user is None:
            return {"id": employee_id, "missing": True}
        events = [event for event in state.get("events", []) if event.get("employee_id") == employee_id]
        return {**user, **score_employee(events)}

    def employees_with_scores(self) -> list[dict]:
        state = self._read()
        employees = [self.employee_score(user["id"]) for user in state.get("users", [])]
        return sorted(employees, key=lambda item: item.get("awareness_points", 0), reverse=True)

    def metrics(self) -> dict:
        state = self._read()
        scored = self.employees_with_scores()
        highest_risk = sorted(scored, key=lambda item: item.get("risk_score", 0), reverse=True)[:3]
        return {
            **campaign_metrics(state.get("users", []), state.get("events", []), state.get("detections", [])),
            "highest_risk": highest_risk,
        }
