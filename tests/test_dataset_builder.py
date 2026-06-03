import unittest

import pandas as pd

from scripts.build_training_dataset import normalize_dataframe


class DatasetBuilderTests(unittest.TestCase):
    def test_normalizes_common_public_dataset_columns(self):
        raw = pd.DataFrame(
            [
                {
                    "Subject": "Password review",
                    "text": "Verify your account password using the linked portal.",
                    "sender": "security@example-work.xyz",
                    "urls": 2,
                    "label": "phishing",
                    "dataset_name": "unit-source",
                },
                {
                    "Subject": "Team update",
                    "text": "The team meeting is moved to Friday afternoon.",
                    "sender": "manager@example.com",
                    "urls": 0,
                    "label": "ham",
                    "dataset_name": "unit-source",
                },
                {
                    "Subject": "Noise",
                    "text": "ignore this",
                    "sender": "unknown",
                    "urls": 0,
                    "label": "garbage",
                    "dataset_name": "unit-source",
                },
            ]
        )

        normalized = normalize_dataframe(raw, min_body_chars=10)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(set(normalized["label"]), {0, 1})
        self.assertEqual(float(normalized.iloc[0]["url_count_hint"]), 2.0)
        self.assertEqual(normalized.iloc[0]["urls"], "")


if __name__ == "__main__":
    unittest.main()
