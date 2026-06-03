from __future__ import annotations

from collections import Counter


EVENT_WEIGHTS = {
    "opened": 5,
    "clicked": 25,
    "submitted": 45,
    "reported": -30,
}

POINT_WEIGHTS = {
    "opened": 1,
    "clicked": -10,
    "submitted": -30,
    "reported": 25,
}


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def score_employee(events: list[dict]) -> dict:
    counts = Counter(event.get("event_type") for event in events)
    risk = 15
    points = 50
    for event_type, count in counts.items():
        risk += EVENT_WEIGHTS.get(event_type, 0) * count
        points += POINT_WEIGHTS.get(event_type, 0) * count

    risk = clamp(risk)
    points = clamp(points)
    if risk >= 75:
        level = "High Risk"
    elif risk >= 45:
        level = "Medium Risk"
    else:
        level = "Low Risk"

    badges: list[str] = []
    if counts["reported"] >= 3:
        badges.append("Phishing Reporter")
    if counts["clicked"] == 0 and counts["submitted"] == 0:
        badges.append("Careful Clicker")
    if counts["submitted"] == 0 and counts["reported"] >= 1:
        badges.append("Credential Guardian")
    if not badges:
        badges.append("Training Started")

    return {
        "risk_score": risk,
        "awareness_points": points,
        "level": level,
        "badges": badges,
        "event_counts": dict(counts),
    }


def campaign_metrics(users: list[dict], events: list[dict], detections: list[dict]) -> dict:
    total_users = len(users)
    counts = Counter(event.get("event_type") for event in events)
    detection_counts = Counter(
        item.get("prediction", {}).get("label", "unknown") for item in detections
    )

    def rate(count: int) -> float:
        if total_users == 0:
            return 0.0
        return round((count / total_users) * 100, 1)

    return {
        "total_users": total_users,
        "total_events": len(events),
        "detection_total": len(detections),
        "phishing_detected": detection_counts.get("phishing", 0),
        "legitimate_detected": detection_counts.get("legitimate", 0),
        "open_rate": rate(counts["opened"]),
        "click_rate": rate(counts["clicked"]),
        "submit_rate": rate(counts["submitted"]),
        "report_rate": rate(counts["reported"]),
    }
