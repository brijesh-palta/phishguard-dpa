# Training Data Sources

This project can train from any CSV, TXT, or Parquet file that has recognizable email text and phishing/legitimate labels.

## Recommended Sources

- Hugging Face `puyang2025/seven-phishing-email-datasets`: normalized Parquet corpus with 203,017 emails from SpamAssassin, CEAS-08, Enron, Ling, and TREC 2005-2007. Labels use `0 = legitimate/ham` and `1 = phishing/spam`.
- Kaggle `avnbluefox/avn-phishing-email-classification-dataset`: clean and noisy variants with subject, sender, receiver, body, URL count, and labels.
- Kaggle `naserabdullahalam/phishing-email-dataset`: combined Enron, Ling, CEAS, Nazario, Nigerian fraud, and SpamAssassin files.

## Safety And Quality Notes

- Public phishing corpora may contain real malicious URLs. Treat them as inert text only.
- Do not commit raw or processed datasets.
- Many public datasets combine phishing and general spam under one positive class. Validate with modern examples before using the model for production filtering.
- Historical corpora can have temporal drift. Retrain with recent authorized reports from your own environment when available.
- Accuracy alone is not enough. Prefer recall, precision, F1, PR-AUC, and the confusion matrix saved by `scripts/train_model.py`.
