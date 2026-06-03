"""Run all phishing detection tests against the running server."""
import sys
import os
import requests
from pathlib import Path

BASE = "http://127.0.0.1:8000"
OUT  = Path(__file__).parent
MIME = {".png": "image/png", ".jpg": "image/jpeg",
        ".pdf": "application/pdf", ".eml": "message/rfc822"}


def upload(path):
    mime = MIME.get(path.suffix, "application/octet-stream")
    r = requests.post(f"{BASE}/api/detect/upload",
                      files={"file": (path.name, path.read_bytes(), mime)})
    return r.json()


def detect_email(subject, body, urls=None, sender="", expected="", reply_to=""):
    payload = {
        "subject": subject, "body": body, "urls": urls or [],
        "sender_email": sender, "expected_domain": expected,
        "reply_to_email": reply_to,
    }
    return requests.post(f"{BASE}/api/detect", json=payload).json()


def bar(score):
    filled = int(score / 10)
    return f"[{'#' * filled}{'.' * (10 - filled)}] {score:>3}/100"


def print_file_result(fname, desc, res):
    lbl   = res.get("label", "?").upper()
    risk  = res.get("risk_level", "?").upper()
    score = res.get("risk_score", 0)
    fa    = res.get("file_analysis", {})
    finds = fa.get("findings", []) or fa.get("auth_findings", [])
    qrls  = fa.get("qr_urls", [])
    kws   = fa.get("keyword_hits", [])
    flag  = "*** PHISHING ***" if lbl == "PHISHING" else "   CLEAN        "
    print(f"\n  [{fname}]")
    print(f"    {desc}")
    print(f"    --> {flag}  |  Risk: {risk:<6}  |  {bar(score)}")
    if qrls:
        print(f"    QR decoded : {qrls[0][:72]}")
    if kws:
        print(f"    Keywords   : {', '.join(kws[:5])}")
    top = [f for f in finds if "No " not in f][:2]
    for fi in top:
        print(f"    [!] {fi[:68]}")


def print_email_result(tag, sender, res):
    lbl   = res.get("label", "?").upper()
    risk  = res.get("risk_level", "?").upper()
    prob  = res.get("phishing_probability", 0)
    sa    = res.get("sender_analysis", {})
    finds = [f for f in sa.get("findings", []) if "No sender" not in f]
    poss  = sa.get("positives", [])
    flag  = "*** PHISHING ***" if lbl == "PHISHING" else "   CLEAN        "
    print(f"\n  [{tag}]")
    print(f"    Sender  : {sender}")
    print(f"    --> {flag}  |  Risk: {risk:<6}  |  Prob: {prob:.0%}")
    for fi in finds[:2]:
        print(f"    [!] {fi[:68]}")
    for p in poss[:1]:
        print(f"    [+] {p[:68]}")


# ── FILE UPLOADS ──────────────────────────────────────────────────────────────
FILE_TESTS = [
    ("01_tracking_pixel.png",        "Tracking pixel (1x1 spy pixel)"),
    ("02_qr_phishing_login.png",     "QR -> Phishing login page (.xyz domain)"),
    ("03_qr_raw_ip_address.png",     "QR -> Raw IP address (185.220.101.47)"),
    ("04_qr_url_shortener.png",      "QR -> bit.ly URL shortener"),
    ("05_qr_open_redirect.png",      "QR -> Open redirect attack"),
    ("06_qr_homograph_paypal.png",   "QR -> Punycode/homograph PayPal domain"),
    ("07_malicious_metadata.png",    "PNG with injected XSS/SQL/PHP metadata"),
    ("08_qr_legitimate_google.png",  "QR -> Legitimate Google URL  (clean)"),
    ("09_qr_fake_microsoft.png",     "QR -> Fake Microsoft OAuth (.club)"),
    ("10_tracking_2x2.png",          "Tracking image (2x2 transparent px)"),
    ("11_pdf_paypal_phishing.pdf",   "PDF - PayPal account suspended phishing"),
    ("12_pdf_invoice_fraud.pdf",     "PDF - Invoice fraud / wire transfer"),
    ("13_pdf_irs_tax_scam.pdf",      "PDF - IRS tax refund scam"),
    ("14_pdf_legitimate_report.pdf", "PDF - Legitimate quarterly report  (clean)"),
    ("15_eml_apple_phishing.eml",    "EML - Apple ID phishing (SPF fail)"),
    ("16_eml_ceo_bec_fraud.eml",     "EML - CEO wire transfer BEC attack"),
    ("17_eml_legitimate_amazon.eml", "EML - Real Amazon order confirm  (clean)"),
    ("18_eml_netflix_scam.eml",      "EML - Netflix billing scam"),
    ("19_eml_microsoft365_phishing.eml", "EML - Microsoft 365 phishing"),
    ("20_eml_legitimate_sprint.eml", "EML - Legitimate sprint notes  (clean)"),
]

# ── EMAIL SENDER TESTS ────────────────────────────────────────────────────────
EMAIL_TESTS = [
    # (tag, subject, body, urls, sender, expected_domain, reply_to)
    ("REAL   | PayPal service@paypal.com",
     "PayPal payment receipt",
     "Your payment of $49.99 to Netflix was processed. Transaction: TX-8827291.",
     ["https://www.paypal.com/activity/payment/TX8827291"],
     "service@paypal.com", "paypal.com", ""),

    ("REAL   | Amazon shipment-tracking@amazon.com",
     "Your order has shipped",
     "Order #113-5829104 will arrive Tuesday. No action needed.",
     ["https://www.amazon.com/gp/your-account/order-history"],
     "shipment-tracking@amazon.com", "amazon.com", ""),

    ("REAL   | Google no-reply@accounts.google.com",
     "New sign-in to your Google Account",
     "A new sign-in from Chrome on Windows was detected. Was this you?",
     ["https://accounts.google.com/signin/activity"],
     "no-reply@accounts.google.com", "google.com", ""),

    ("REAL   | Microsoft account-security-noreply@...",
     "Microsoft account security alert",
     "Your Microsoft account password was recently changed from a verified device.",
     ["https://account.microsoft.com/security"],
     "account-security-noreply@accountprotection.microsoft.com", "microsoft.com", ""),

    ("REAL   | Apple no_reply@email.apple.com",
     "Your Apple ID was used to sign in",
     "Your Apple ID was used to sign in to iCloud on an iPhone 15. Was this you?",
     ["https://appleid.apple.com/account/manage"],
     "no_reply@email.apple.com", "apple.com", ""),

    ("REAL   | Netflix info@account.netflix.com",
     "Your Netflix subscription renewed",
     "Your monthly subscription has been successfully renewed. Enjoy watching!",
     ["https://www.netflix.com/YourAccount"],
     "info@account.netflix.com", "netflix.com", ""),

    ("SPOOF  | PayPal -> security@paypa1.com",
     "URGENT: Verify your PayPal account immediately",
     "Your account is limited. Verify now or lose access permanently.",
     ["http://paypa1-secure-login.com/verify"],
     "security@paypa1.com", "paypal.com", ""),

    ("SPOOF  | Amazon -> no-reply@amaz0n.com",
     "Amazon account locked - verify now",
     "Unusual activity detected. Confirm your identity to restore access.",
     ["http://amaz0n-account-secure.xyz/login"],
     "no-reply@amaz0n.com", "amazon.com", ""),

    ("SPOOF  | Google -> security@g00gle.com",
     "Google Account suspended - action required",
     "Your Google account will be deactivated. Confirm your details now.",
     ["http://g00gle-accounts-verify.top/confirm"],
     "security@g00gle.com", "google.com", ""),

    ("SPOOF  | Microsoft -> noreply@micros0ft.com",
     "Microsoft 365 license expired",
     "Your Microsoft 365 subscription expired. Renew now to avoid data loss.",
     ["http://micros0ft-365-renew.xyz/license"],
     "noreply@micros0ft.com", "microsoft.com", ""),

    ("SPOOF  | Apple via subdomain apple.com.security-alert.top",
     "Apple ID locked - verify immediately",
     "Your Apple ID was locked after multiple failed attempts. Click to verify.",
     ["http://apple-id-secure-verify.xyz/unlock"],
     "security@apple.com.security-alert.top", "apple.com", "support@gmail.com"),

    ("SPOOF  | Netflix -> billing@netfl1x-payments.com",
     "Netflix payment failed - account suspended",
     "We could not process your payment. Update billing info within 24 hours.",
     ["http://netfl1x-billing-secure.click/update"],
     "billing@netfl1x-payments.com", "netflix.com", "support@outlook.com"),

    ("SPOOF  | IRS via Gmail irs.refunds@gmail.com",
     "IRS Tax Refund of $2840 pending",
     "You have an unclaimed tax refund for 2023. Verify SSN and bank account now.",
     ["http://irs-refund-claim.loan/verify"],
     "irs.refunds@gmail.com", "irs.gov", ""),

    ("SPOOF  | CEO BEC ceo@gmail.com + protonmail reply-to",
     "Urgent: Confidential wire transfer needed today",
     "Wire $87,500 to our legal firm before 3pm today. Confidential. Confirm done.",
     [], "ceo@gmail.com", "company.com", "ceo.payments@protonmail.com"),

    ("SPOOF  | Subdomain support@paypal.evil-secure.xyz",
     "PayPal: your account needs verification",
     "Your PayPal account requires immediate verification to stay active.",
     ["http://paypal.evil-secure.xyz/verify"],
     "support@paypal.evil-secure.xyz", "paypal.com", ""),
]


def main():
    sep = "=" * 70
    print(f"\n{sep}")
    print("  PHISHGUARD — FULL DETECTION TEST SUITE")
    print(f"{sep}\n")

    # Section 1: File uploads
    print("-" * 70)
    print("  SECTION 1: File Uploads (Images / PDFs / EML files)")
    print("-" * 70)
    for fname, desc in FILE_TESTS:
        path = OUT / fname
        if not path.exists():
            print(f"\n  [{fname}] -- file missing, skip")
            continue
        try:
            res = upload(path)
            print_file_result(fname, desc, res)
        except Exception as exc:
            print(f"\n  [{fname}] ERROR: {exc}")

    # Section 2: Email sender tests
    print(f"\n{'-' * 70}")
    print("  SECTION 2: Official & Spoofed Email Sender Tests")
    print("-" * 70)
    for row in EMAIL_TESTS:
        tag, subject, body, urls, sender, expected, reply_to = row
        try:
            res = detect_email(subject, body, urls, sender, expected, reply_to)
            print_email_result(tag, sender, res)
        except Exception as exc:
            print(f"\n  [{tag}] ERROR: {exc}")

    print(f"\n{sep}")
    print("  ALL TESTS COMPLETE")
    print(sep)


if __name__ == "__main__":
    main()
