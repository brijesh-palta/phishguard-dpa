from pathlib import Path
import unittest

from phishguard.detector import PhishingDetectorService, train_model


BASE_DIR = Path(__file__).resolve().parents[1]


class DetectorTests(unittest.TestCase):
    def test_detector_flags_obvious_phishing(self):
        model_path = BASE_DIR / "artifacts" / "test_detector_model.joblib"
        train_model(BASE_DIR / "data" / "sample_emails.csv", model_path)
        detector = PhishingDetectorService(BASE_DIR / "data" / "sample_emails.csv", model_path)

        result = detector.predict(
            subject="Urgent account locked",
            body="Verify your password immediately or your account will be suspended.",
            urls=["http://secure-login.example-work.xyz/verify"],
        )

        self.assertEqual(result["label"], "phishing")
        self.assertGreaterEqual(result["phishing_probability"], 0.5)

    def test_detector_allows_routine_message(self):
        model_path = BASE_DIR / "artifacts" / "test_detector_model.joblib"
        train_model(BASE_DIR / "data" / "sample_emails.csv", model_path)
        detector = PhishingDetectorService(BASE_DIR / "data" / "sample_emails.csv", model_path)

        result = detector.predict(
            subject="Team lunch schedule",
            body="The office lunch is planned for Friday at 12:30. Please reply with dietary notes.",
            urls=[],
        )

        self.assertEqual(result["label"], "legitimate")


if __name__ == "__main__":
    unittest.main()
