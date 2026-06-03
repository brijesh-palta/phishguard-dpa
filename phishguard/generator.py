from __future__ import annotations

import random
from datetime import datetime, timezone


SCENARIOS = {
    "password_reset": {
        "subject": "Action required: password reset review",
        "body": (
            "Hi {name},\n\n"
            "Your training account has been selected for a password reset drill. "
            "Review the message, inspect the sender and link, and decide whether it should be reported.\n\n"
            "Training link: {link}\n\n"
            "Security Awareness Team"
        ),
        "red_flags": [
            "Uses account access pressure",
            "Asks the reader to inspect the link destination",
            "Can be used to test reporting behavior without collecting real passwords",
        ],
    },
    "invoice": {
        "subject": "Invoice review requested before end of day",
        "body": (
            "Hi {name},\n\n"
            "Please review this simulated invoice notice before the end of day. "
            "This is a training email, so do not enter real credentials anywhere.\n\n"
            "Training link: {link}\n\n"
            "Finance Awareness Drill"
        ),
        "red_flags": [
            "Financial topic creates pressure",
            "Deadline wording can trigger rushed clicks",
            "A safe training link should never request real payment details",
        ],
    },
    "hr_policy": {
        "subject": "HR policy acknowledgement exercise",
        "body": (
            "Hi {name},\n\n"
            "This simulated HR notice asks you to review a policy acknowledgement page. "
            "Check whether the sender, domain, and request make sense before interacting.\n\n"
            "Training link: {link}\n\n"
            "People Operations Training"
        ),
        "red_flags": [
            "Impersonates an internal department",
            "Encourages checking domain and sender alignment",
            "Useful for teaching safe reporting habits",
        ],
    },
    "cloud_storage": {
        "subject": "Shared document security training",
        "body": (
            "Hi {name},\n\n"
            "A simulated cloud document has been shared with you for awareness training. "
            "Inspect the link and report the message if it looks unusual.\n\n"
            "Training link: {link}\n\n"
            "Cloud Security Training"
        ),
        "red_flags": [
            "Mimics common document-share lures",
            "Teaches users to inspect links before login",
            "No real file or credential collection is involved",
        ],
    },
}

DIFFICULTY_HINTS = {
    "easy": ["Look for urgency", "Check whether the link domain matches the sender"],
    "medium": ["Compare the wording with normal company messages", "Hover over links before clicking"],
    "hard": ["Check small domain spelling changes", "Look for mismatched tone, timing, and request context"],
}


def generate_training_challenge(
    scenario: str | None = None,
    difficulty: str = "medium",
    employee_name: str | None = None,
) -> dict:
    scenario_key = scenario if scenario in SCENARIOS else random.choice(list(SCENARIOS))
    difficulty_key = difficulty if difficulty in DIFFICULTY_HINTS else "medium"
    name = employee_name or "Learner"
    tracking_id = random.randint(10000, 99999)
    safe_link = f"http://localhost:8000/training/track/{tracking_id}"
    template = SCENARIOS[scenario_key]

    return {
        "scenario": scenario_key,
        "difficulty": difficulty_key,
        "subject": template["subject"],
        "body": template["body"].format(name=name, link=safe_link),
        "red_flags": template["red_flags"],
        "hints": DIFFICULTY_HINTS[difficulty_key],
        "points_available": {"report": 25, "identify_all_red_flags": 15, "avoid_click": 10},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety_note": "Training content only. Do not collect real credentials or send outside authorized testing.",
    }
