from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DetectionRequest(BaseModel):
    subject: str = Field(default="", max_length=300)
    body: str = Field(default="", max_length=10000)
    urls: list[str] = Field(default_factory=list)
    sender_email: str = Field(default="", max_length=320)
    reply_to_email: str = Field(default="", max_length=320)
    expected_domain: str = Field(default="", max_length=255)


class EventRequest(BaseModel):
    employee_id: str
    campaign_id: str = "camp-demo"
    event_type: Literal["opened", "clicked", "submitted", "reported"]


class TrainingRequest(BaseModel):
    scenario: str | None = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    employee_name: str | None = None
