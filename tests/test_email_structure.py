from pathlib import Path
import unittest

from fastapi.testclient import TestClient

from app import app
from phishguard.detector import PhishingDetectorService, analyze_email_structure, train_model
from phishguard.generator import generate_training_challenge


BASE_DIR = Path(__file__).resolve().parents[1]


class EmailStructureTests(unittest.TestCase):
    def test_html_mismatched_link_and_attachment_are_flagged(self):
        result = analyze_email_structure(
            html_body=(
                '<a href="http://secure-login.example-work.xyz/verify">'
                "https://employee.example.com/security</a>"
                '<img src="http://secure-login.example-work.xyz/open-pixel.gif" width="1" height="1">'
            ),
            urls=[],
            image_urls=[],
            attachment_names=["benefits-update.pdf.exe"],
        )

        self.assertEqual(result["verdict"], "suspicious")
        self.assertGreaterEqual(result["risk_score"], 60)
        joined = " ".join(result["findings"]).lower()
        self.assertIn("link text", joined)
        self.assertIn("risky file type", joined)

    def test_detector_combines_structure_risk_with_model_score(self):
        model_path = BASE_DIR / "artifacts" / "test_structure_model.joblib"
        train_model(BASE_DIR / "data" / "sample_emails.csv", model_path)
        detector = PhishingDetectorService(BASE_DIR / "data" / "sample_emails.csv", model_path)

        result = detector.predict(
            subject="Document review",
            body="Please review the document notice.",
            html_body=(
                '<a href="http://docs-review-secure.top/account">'
                "https://docs.example.com/review</a>"
            ),
            urls=[],
            image_urls=["http://docs-review-secure.top/open-pixel.gif"],
            attachment_names=["document-review.html"],
        )

        self.assertEqual(result["label"], "phishing")
        self.assertGreaterEqual(result["structure_probability"], 0.6)
        self.assertIn("structure_analysis", result)

    def test_generator_returns_html_links_and_images(self):
        result = generate_training_challenge(
            scenario="cloud_storage",
            difficulty="hard",
            employee_name="Ava",
            company_name="Example Co",
            base_url="http://localhost:8000",
        )

        self.assertIn("<html", result["html_body"])
        self.assertGreaterEqual(len(result["links"]), 2)
        self.assertGreaterEqual(len(result["images"]), 2)
        self.assertIn("gophish_template", result)

    def test_generated_training_links_are_served(self):
        client = TestClient(app)

        track_response = client.get("/training/track/12345?scenario=cloud_storage")
        tips_response = client.get("/training/tips?scenario=cloud_storage")

        self.assertEqual(track_response.status_code, 200)
        self.assertEqual(tips_response.status_code, 200)
        self.assertIn("Authorized training", track_response.text)
        self.assertIn("Safety Tips", tips_response.text)


if __name__ == "__main__":
    unittest.main()
