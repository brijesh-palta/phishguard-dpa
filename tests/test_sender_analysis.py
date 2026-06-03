import unittest

from phishguard.detector import PhishingDetectorService, analyze_sender, train_model
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


class SenderAnalysisTests(unittest.TestCase):
    def test_personal_sender_is_suspicious_when_company_domain_is_expected(self):
        result = analyze_sender(
            sender_email="it.support@gmail.com",
            reply_to_email="it.support@gmail.com",
            expected_domain="deakin.edu.au",
        )

        self.assertEqual(result["verdict"], "suspicious")
        self.assertGreaterEqual(result["risk_score"], 60)
        self.assertIn("personal/free", " ".join(result["findings"]))

    def test_matching_company_sender_is_trusted(self):
        result = analyze_sender(
            sender_email="security@deakin.edu.au",
            reply_to_email="security@deakin.edu.au",
            expected_domain="deakin.edu.au",
        )

        self.assertEqual(result["verdict"], "trusted")
        self.assertLess(result["risk_score"], 30)

    def test_detector_flags_legit_looking_content_from_fake_sender(self):
        model_path = BASE_DIR / "artifacts" / "test_sender_model.joblib"
        train_model(BASE_DIR / "data" / "sample_emails.csv", model_path)
        detector = PhishingDetectorService(BASE_DIR / "data" / "sample_emails.csv", model_path)

        result = detector.predict(
            subject="Monthly payslip available",
            body="Your monthly payslip is available in the official employee portal.",
            urls=["https://employee.example.com/payroll"],
            sender_email="payroll.support@gmail.com",
            reply_to_email="payroll.support@gmail.com",
            expected_domain="example.com",
        )

        self.assertEqual(result["label"], "phishing")
        self.assertGreaterEqual(result["sender_analysis"]["risk_score"], 60)


if __name__ == "__main__":
    unittest.main()
