from __future__ import annotations

import json
import os
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen


def get_gophish_status() -> dict:
    base_url = os.getenv("GOPHISH_BASE_URL", "https://127.0.0.1:3333").rstrip("/")
    api_key = os.getenv("GOPHISH_API_KEY", "")
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
