import unittest

from phishguard.risk import score_employee


class RiskTests(unittest.TestCase):
    def test_reporting_reduces_risk_and_awards_badge(self):
        result = score_employee(
            [
                {"event_type": "reported"},
                {"event_type": "reported"},
                {"event_type": "reported"},
            ]
        )

        self.assertEqual(result["risk_score"], 0)
        self.assertIn("Phishing Reporter", result["badges"])

    def test_click_and_submit_raise_risk(self):
        result = score_employee(
            [
                {"event_type": "opened"},
                {"event_type": "clicked"},
                {"event_type": "submitted"},
            ]
        )

        self.assertGreaterEqual(result["risk_score"], 80)
        self.assertEqual(result["level"], "High Risk")


if __name__ == "__main__":
    unittest.main()
