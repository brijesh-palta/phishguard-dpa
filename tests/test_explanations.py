import unittest

from phishguard.detector import explain_prediction


class ExplanationTests(unittest.TestCase):
    def test_negated_urgent_phrase_is_not_flagged(self):
        reasons = explain_prediction(
            subject="Monthly payslip available",
            body="Your payslip is available in the official portal. No urgent action is required.",
            urls=["https://employee.example.com/payroll"],
        )

        self.assertNotIn("urgent", " ".join(reasons).lower())


if __name__ == "__main__":
    unittest.main()
