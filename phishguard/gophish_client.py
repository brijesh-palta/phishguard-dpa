from __future__ import annotations

import json
import os
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen


def get_gophish_status() -> dict:
    base_url = os.getenv("GOPHISH_BASE_URL", "https://127.0.0.1:3333").strip().rstrip("/")
    api_key = os.getenv("GOPHISH_API_KEY", "").strip()
    if not api_key:
        return {
            "configured": False,
            "reachable": False,
            "message": "Set GOPHISH_API_KEY to enable live GoPhish API checks.",
            "base_url": base_url,
        }

    request = Request(f"{base_url}/api/campaigns/?api_key={api_key}")
    context = ssl._create_unverified_context()
    try:
        with urlopen(request, context=context, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {
            "configured": True,
            "reachable": True,
            "base_url": base_url,
            "campaign_count": len(payload),
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "configured": True,
            "reachable": False,
            "base_url": base_url,
            "message": str(exc),
        }


def _gophish_request(path: str) -> dict | list:
    base_url = os.getenv("GOPHISH_BASE_URL", "https://127.0.0.1:3333").strip().rstrip("/")
    api_key = os.getenv("GOPHISH_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GOPHISH_API_KEY is not configured")

    request = Request(f"{base_url}{path}?api_key={api_key}")
    context = ssl._create_unverified_context()
    with urlopen(request, context=context, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def get_gophish_campaigns() -> list[dict]:
    raw = _gophish_request("/api/campaigns")
    if not isinstance(raw, list):
        raise ValueError("Unexpected GoPhish campaigns response")
    return [
        {
            "id": str(item.get("id")),
            "name": item.get("name"),
            "status": item.get("status"),
            "created_at": item.get("created_date"),
            "send_date": item.get("send_date"),
            "results": item.get("results", {}),
        }
        for item in raw
    ]


def get_gophish_campaign_details(campaign_id: str) -> dict:
    raw = _gophish_request(f"/api/campaigns/{campaign_id}")
    if isinstance(raw, dict) and "campaign" in raw and isinstance(raw["campaign"], dict):
        raw = raw["campaign"]
    if not isinstance(raw, dict):
        raise ValueError("Unexpected GoPhish campaign detail response")
    return raw


def get_gophish_campaign_results(campaign_id: str) -> dict:
    raw = _gophish_request(f"/api/campaigns/{campaign_id}/results")
    if not isinstance(raw, dict):
        raise ValueError("Unexpected GoPhish campaign results response")
    return {
        "campaign_id": campaign_id,
        "summary": raw.get("summary", {}),
        "unsubscribed": raw.get("unsubscribed", []),
        "clicked": raw.get("clicked", []),
        "reported": raw.get("reported", []),
    }
