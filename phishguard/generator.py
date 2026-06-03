from __future__ import annotations

import random
from datetime import datetime, timezone
from html import escape
from urllib.parse import quote, urlparse


SCENARIOS = {
    "password_reset": {
        "subject": "{company_name} account security review",
        "department": "Security Operations",
        "hero_image": "security-banner.svg",
        "hero_alt": "Account security dashboard illustration",
        "headline": "Account security review",
        "intro": (
            "A sign-in review has been scheduled for {name}. Use the training page to inspect "
            "the sender, link destination, and request details before deciding what to do."
        ),
        "cta_label": "Review security notice",
        "secondary_label": "Open reporting guide",
        "red_flags": [
            "Creates account-access pressure",
            "Uses a button-style call to action",
            "Includes a trackable image and multiple links for awareness analysis",
        ],
    },
    "invoice": {
        "subject": "{company_name} invoice review request",
        "department": "Finance Operations",
        "hero_image": "invoice-banner.svg",
        "hero_alt": "Invoice review illustration",
        "headline": "Invoice review requested",
        "intro": (
            "A vendor invoice drill is ready for {name}. Review the training page and decide "
            "whether the message should be trusted, reported, or ignored."
        ),
        "cta_label": "Review invoice drill",
        "secondary_label": "View finance policy",
        "red_flags": [
            "Financial language can encourage rushed action",
            "A link-driven workflow should be verified before use",
            "Safe training emails must never request payment details",
        ],
    },
    "hr_policy": {
        "subject": "{company_name} HR policy acknowledgement",
        "department": "People Operations",
        "hero_image": "hr-banner.svg",
        "hero_alt": "Policy acknowledgement illustration",
        "headline": "Policy acknowledgement exercise",
        "intro": (
            "{name}, this simulated HR notice asks you to inspect the sender, domain, and "
            "request context before interacting with the acknowledgement link."
        ),
        "cta_label": "Review policy exercise",
        "secondary_label": "Contact HR help",
        "red_flags": [
            "Impersonates an internal department",
            "Uses a routine HR workflow to lower suspicion",
            "Teaches employees to compare sender, domain, and request context",
        ],
    },
    "cloud_storage": {
        "subject": "{company_name} shared document exercise",
        "department": "Cloud Security",
        "hero_image": "cloud-banner.svg",
        "hero_alt": "Cloud document sharing illustration",
        "headline": "Shared document security exercise",
        "intro": (
            "A simulated cloud document has been shared with {name}. Inspect the link, image, "
            "and sender details before choosing whether to report it."
        ),
        "cta_label": "Open document drill",
        "secondary_label": "Read cloud safety tips",
        "red_flags": [
            "Mimics common document-share lures",
            "Encourages checking link destinations before login",
            "No real file or credential collection is involved",
        ],
    },
}

DIFFICULTY_HINTS = {
    "easy": ["Look for urgency", "Check whether the link domain matches the sender"],
    "medium": ["Compare the wording with normal company messages", "Hover over links before clicking"],
    "hard": ["Check small domain spelling changes", "Look for mismatched tone, timing, and request context"],
}


def _safe_base_url(value: str | None) -> str:
    candidate = (value or "http://localhost:8000").strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "http://localhost:8000"
    return candidate


def _asset_url(base_url: str, filename: str) -> str:
    return f"{base_url}/static/training-assets/{quote(filename)}"


def _plain_text_body(
    template: dict,
    name: str,
    company_name: str,
    primary_link: str,
    secondary_link: str,
) -> str:
    return (
        f"Hi {name},\n\n"
        f"{template['intro'].format(name=name)}\n\n"
        f"{template['cta_label']}: {primary_link}\n"
        f"{template['secondary_label']}: {secondary_link}\n\n"
        f"{template['department']}\n"
        f"{company_name}\n\n"
        "Authorized security awareness simulation. Do not enter real credentials."
    )


def _html_email(
    template: dict,
    name: str,
    company_name: str,
    primary_link: str,
    secondary_link: str,
    hero_image: str,
    tracking_pixel: str,
) -> str:
    safe_company = escape(company_name)
    safe_name = escape(name)
    safe_department = escape(template["department"])
    safe_headline = escape(template["headline"])
    safe_intro = escape(template["intro"].format(name=name))
    safe_cta = escape(template["cta_label"])
    safe_secondary = escape(template["secondary_label"])
    safe_hero_alt = escape(template["hero_alt"])

    return f"""<!doctype html>
<html lang="en">
  <body style="margin:0;background:#eef3f8;font-family:Arial,Helvetica,sans-serif;color:#17212b;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef3f8;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="640" cellspacing="0" cellpadding="0" style="width:640px;max-width:100%;background:#ffffff;border:1px solid #d9e2ec;">
            <tr>
              <td style="padding:18px 22px;background:#142033;color:#ffffff;">
                <div style="font-size:12px;text-transform:uppercase;letter-spacing:0;color:#98b5d7;">{safe_department}</div>
                <div style="font-size:20px;font-weight:700;margin-top:4px;">{safe_company}</div>
              </td>
            </tr>
            <tr>
              <td>
                <img src="{hero_image}" alt="{safe_hero_alt}" width="640" style="display:block;width:100%;max-width:640px;border:0;" />
              </td>
            </tr>
            <tr>
              <td style="padding:26px 28px 8px;">
                <div style="font-size:13px;color:#647386;">Hi {safe_name},</div>
                <h1 style="margin:10px 0 10px;font-size:25px;line-height:1.2;color:#17212b;">{safe_headline}</h1>
                <p style="margin:0 0 18px;font-size:15px;line-height:1.55;color:#314154;">{safe_intro}</p>
                <a href="{primary_link}" style="display:inline-block;background:#2368d1;color:#ffffff;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:6px;">{safe_cta}</a>
                <p style="margin:18px 0 0;font-size:13px;line-height:1.5;color:#647386;">
                  Need context? <a href="{secondary_link}" style="color:#2368d1;">{safe_secondary}</a>
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 24px;">
                <div style="border-top:1px solid #d9e2ec;padding-top:14px;font-size:12px;line-height:1.45;color:#647386;">
                  Authorized security awareness simulation. Do not enter real credentials.
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    <img src="{tracking_pixel}" alt="" width="1" height="1" style="display:none;width:1px;height:1px;" />
  </body>
</html>"""


def generate_training_challenge(
    scenario: str | None = None,
    difficulty: str = "medium",
    employee_name: str | None = None,
    company_name: str = "Example Co",
    base_url: str = "http://localhost:8000",
) -> dict:
    scenario_key = scenario if scenario in SCENARIOS else random.choice(list(SCENARIOS))
    difficulty_key = difficulty if difficulty in DIFFICULTY_HINTS else "medium"
    name = (employee_name or "Learner").strip() or "Learner"
    company = (company_name or "Example Co").strip() or "Example Co"
    base = _safe_base_url(base_url)
    tracking_id = random.randint(10000, 99999)
    template = SCENARIOS[scenario_key]

    primary_link = f"{base}/training/track/{tracking_id}?scenario={quote(scenario_key)}"
    secondary_link = f"{base}/training/tips?scenario={quote(scenario_key)}"
    hero_image = _asset_url(base, template["hero_image"])
    tracking_pixel = f"{_asset_url(base, 'open-pixel.svg')}?tid={tracking_id}"
    subject = template["subject"].format(company_name=company)
    body = _plain_text_body(template, name, company, primary_link, secondary_link)
    html_body = _html_email(template, name, company, primary_link, secondary_link, hero_image, tracking_pixel)

    links = [
        {"label": template["cta_label"], "url": primary_link, "purpose": "primary_training_cta"},
        {"label": template["secondary_label"], "url": secondary_link, "purpose": "supporting_awareness_content"},
    ]
    images = [
        {"role": "hero", "url": hero_image, "alt_text": template["hero_alt"]},
        {"role": "open_tracking_pixel", "url": tracking_pixel, "alt_text": ""},
    ]

    return {
        "scenario": scenario_key,
        "difficulty": difficulty_key,
        "subject": subject,
        "body": body,
        "plain_text_body": body,
        "html_body": html_body,
        "links": links,
        "images": images,
        "tracking_id": tracking_id,
        "landing_page_url": primary_link,
        "red_flags": template["red_flags"],
        "hints": DIFFICULTY_HINTS[difficulty_key],
        "points_available": {"report": 25, "identify_all_red_flags": 15, "avoid_click": 10},
        "gophish_template": {
            "name": f"{company} - {scenario_key.replace('_', ' ').title()} Drill",
            "subject": subject,
            "text": body,
            "html": html_body,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety_note": "Training content only. Do not collect real credentials or send outside authorized testing.",
    }
