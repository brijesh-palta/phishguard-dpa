from __future__ import annotations

import io
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from phishguard.detector import (
    analyze_file_content,
    analyze_image_content,
    analyze_pdf_content,
    parse_eml_bytes,
)


def _make_pdf(text: str, url: str | None = None) -> bytes:
    """Create a minimal single-page PDF containing text and an optional link."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=12)
    if url:
        rect = fitz.Rect(72, 120, 300, 140)
        page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": url})
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


def _make_qr_image(data: str) -> bytes:
    """Create a PNG image containing a QR code for *data*."""
    import qrcode  # type: ignore

    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()


def _make_plain_png() -> bytes:
    """Create a small solid-colour PNG with no QR code."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_tracking_pixel() -> bytes:
    """Create a 1x1 PNG (tracking pixel)."""
    from PIL import Image

    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_eml(
    subject: str = "Test",
    sender: str = "sender@example.com",
    reply_to: str = "",
    body: str = "Hello",
    spf: str = "",
) -> bytes:
    lines = [
        f"From: {sender}",
        f"Subject: {subject}",
        "MIME-Version: 1.0",
        "Content-Type: text/plain; charset=utf-8",
    ]
    if reply_to:
        lines.append(f"Reply-To: {reply_to}")
    if spf:
        lines.append(f"Received-SPF: {spf}")
    lines += ["", body]
    return "\r\n".join(lines).encode()


class PdfAnalysisTests(unittest.TestCase):
    def test_clean_pdf_is_low_risk(self):
        pdf_bytes = _make_pdf("Hello, please find the meeting notes attached.")
        result = analyze_pdf_content(pdf_bytes)
        self.assertIn(result["verdict"], {"low", "review"})
        self.assertLess(result["risk_score"], 60)

    def test_phishing_pdf_is_flagged(self):
        text = (
            "URGENT: Your account is suspended. Verify your password immediately. "
            "Login here or your account will be locked. Final notice: act now."
        )
        pdf_bytes = _make_pdf(text, url="http://secure-login-reset.xyz/verify")
        result = analyze_pdf_content(pdf_bytes)
        self.assertGreaterEqual(result["risk_score"], 30)
        self.assertTrue(len(result["keyword_hits"]) > 0)

    def test_pdf_with_suspicious_url_raises_risk(self):
        pdf_bytes = _make_pdf("Click the link below.", url="http://bit.ly/xyz123")
        result = analyze_pdf_content(pdf_bytes)
        self.assertGreaterEqual(result["risk_score"], 15)
        self.assertGreater(result["embedded_url_count"], 0)

    def test_invalid_bytes_returns_error_result(self):
        result = analyze_pdf_content(b"not a pdf")
        self.assertIn("findings", result)
        self.assertTrue(len(result["findings"]) > 0)


class ImageAnalysisTests(unittest.TestCase):
    def test_clean_image_is_low_risk(self):
        png_bytes = _make_plain_png()
        result = analyze_image_content(png_bytes, "photo.png")
        self.assertIn(result["verdict"], {"low", "review"})
        self.assertEqual(result["qr_urls"], [])

    def test_tracking_pixel_is_flagged(self):
        pixel_bytes = _make_tracking_pixel()
        result = analyze_image_content(pixel_bytes, "open.png")
        self.assertGreater(result["risk_score"], 0)
        joined = " ".join(result["findings"]).lower()
        self.assertIn("tracking pixel", joined)

    def test_corrupt_bytes_return_error_result(self):
        result = analyze_image_content(b"\x00\x01\x02", "bad.png")
        self.assertIn("findings", result)


class EmlParsingTests(unittest.TestCase):
    def test_parses_subject_and_sender(self):
        eml = _make_eml(subject="Hello world", sender="alice@example.com")
        parsed = parse_eml_bytes(eml)
        self.assertIn("Hello world", parsed["subject"])
        self.assertIn("alice@example.com", parsed["sender"])

    def test_spf_fail_is_detected(self):
        eml = _make_eml(spf="Fail (spf.example.com: domain does not designate)")
        parsed = parse_eml_bytes(eml)
        self.assertTrue(parsed["spf_fail"])

    def test_spf_pass_is_not_flagged(self):
        eml = _make_eml(spf="Pass (spf.example.com)")
        parsed = parse_eml_bytes(eml)
        self.assertFalse(parsed["spf_fail"])


class FileContentDispatcherTests(unittest.TestCase):
    def test_pdf_dispatched_correctly(self):
        pdf_bytes = _make_pdf("Meeting notes for Q3 review.")
        result = analyze_file_content("notes.pdf", pdf_bytes)
        self.assertEqual(result["type"], "pdf")
        self.assertIn("risk_score", result)

    def test_image_dispatched_correctly(self):
        png_bytes = _make_plain_png()
        result = analyze_file_content("logo.png", png_bytes)
        self.assertEqual(result["type"], "image")

    def test_eml_dispatched_correctly(self):
        eml_bytes = _make_eml(subject="Test", sender="a@b.com")
        result = analyze_file_content("test.eml", eml_bytes)
        self.assertEqual(result["type"], "eml")
        self.assertIn("sender_analysis", result)

    def test_unsupported_type_returns_graceful_result(self):
        result = analyze_file_content("file.docx", b"some bytes")
        self.assertEqual(result["type"], "unsupported")
        self.assertEqual(result["risk_score"], 0)


class UploadEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_upload_clean_pdf_returns_200(self):
        pdf_bytes = _make_pdf("Quarterly report summary for review.")
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("report.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("label", data)
        self.assertIn("risk_score", data)
        self.assertEqual(data["file_type"], "pdf")

    def test_upload_phishing_pdf_is_flagged(self):
        text = "URGENT: Verify your password or account will be suspended. Click http://evil.xyz/login"
        pdf_bytes = _make_pdf(text, url="http://evil.xyz/login")
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["risk_score"], 0)

    def test_upload_image_returns_200(self):
        png_bytes = _make_plain_png()
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("logo.png", png_bytes, "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["file_type"], "image")

    def test_upload_eml_returns_200(self):
        eml_bytes = _make_eml(subject="Team sync", sender="boss@company.com")
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("email.eml", eml_bytes, "message/rfc822")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["file_type"], "eml")

    def test_upload_unsupported_extension_returns_400(self):
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("macro.docx", b"data", "application/octet-stream")},
        )
        self.assertEqual(response.status_code, 400)

    def test_upload_with_suspicious_sender_raises_risk(self):
        pdf_bytes = _make_pdf("Meeting agenda.")
        response = self.client.post(
            "/api/detect/upload",
            files={"file": ("agenda.pdf", pdf_bytes, "application/pdf")},
            data={"sender_email": "hr@paypa1-secure.xyz", "expected_domain": "paypal.com"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data["sender_analysis"])
        self.assertGreaterEqual(data["risk_score"], 60)


if __name__ == "__main__":
    unittest.main()
