from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from email.utils import parseaddr
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler


PHISHING_KEYWORDS = {
    "urgent",
    "verify",
    "password",
    "suspended",
    "locked",
    "confirm",
    "account",
    "security",
    "invoice",
    "payment",
    "limited",
    "expire",
    "credential",
    "login",
    "wallet",
    "prize",
    "winner",
    "refund",
}

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "cutt.ly", "is.gd"}
SUSPICIOUS_TLDS = {".zip", ".mov", ".top", ".xyz", ".club", ".click", ".work", ".loan"}
FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "zoho.com",
    "mail.com",
    "yandex.com",
}
COMMON_PUBLIC_SUFFIX_GUESSES = {
    "co.uk",
    "com.au",
    "net.au",
    "org.au",
    "edu.au",
    "co.in",
    "ac.in",
    "gov.in",
    "co.nz",
}


def _normalize_urls(urls: str | Iterable[str] | None) -> list[str]:
    if urls is None:
        return []
    if isinstance(urls, str):
        pieces = re.split(r"[\s,]+", urls)
        return [piece.strip() for piece in pieces if piece.strip()]
    return [str(url).strip() for url in urls if str(url).strip()]


def _normalize_domain(value: str | None) -> str:
    if not value:
        return ""
    candidate = str(value).strip().lower().strip("<> ,")
    if "@" in candidate:
        candidate = parseaddr(candidate)[1].split("@")[-1]
    if "://" in candidate:
        candidate = urlparse(candidate).netloc
    candidate = candidate.split(":")[0].strip(".")
    try:
        candidate = candidate.encode("idna").decode("ascii")
    except UnicodeError:
        pass
    return candidate


def _email_domain(value: str | None) -> tuple[str, str, bool]:
    address = parseaddr(value or "")[1].lower().strip()
    valid = bool(re.match(r"^[a-z0-9._%+\-']+@[a-z0-9.-]+\.[a-z]{2,}$", address))
    domain = _normalize_domain(address.split("@")[-1] if "@" in address else "")
    return address, domain, valid


def _registrable_domain(domain: str) -> str:
    domain = _normalize_domain(domain)
    parts = [part for part in domain.split(".") if part]
    if len(parts) < 2:
        return domain
    suffix = ".".join(parts[-2:])
    if suffix in COMMON_PUBLIC_SUFFIX_GUESSES and len(parts) >= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _root_label(domain: str) -> str:
    registered = _registrable_domain(domain)
    parts = registered.split(".")
    return parts[0] if parts else ""


def _domain_matches(sender_domain: str, expected_domain: str) -> bool:
    sender_domain = _normalize_domain(sender_domain)
    expected_domain = _normalize_domain(expected_domain)
    if not sender_domain or not expected_domain:
        return False
    return sender_domain == expected_domain or sender_domain.endswith(f".{expected_domain}")


def _looks_like_domain(sender_domain: str, expected_domain: str) -> bool:
    sender_root = _root_label(sender_domain)
    expected_root = _root_label(expected_domain)
    if not sender_root or not expected_root:
        return False
    skeleton = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s"})
    sender_skeleton = sender_root.translate(skeleton).replace("-", "")
    expected_skeleton = expected_root.translate(skeleton).replace("-", "")
    similarity = SequenceMatcher(None, sender_skeleton, expected_skeleton).ratio()
    return (
        similarity >= 0.78
        or expected_skeleton in sender_skeleton
        or sender_skeleton in expected_skeleton
    )


def analyze_sender(
    sender_email: str | None = None,
    reply_to_email: str | None = None,
    expected_domain: str | None = None,
) -> dict:
    sender_address, sender_domain, valid_sender = _email_domain(sender_email)
    reply_to_address, reply_to_domain, valid_reply_to = _email_domain(reply_to_email)
    expected = _normalize_domain(expected_domain)
    findings: list[str] = []
    positives: list[str] = []
    risk_score = 0

    if not sender_email:
        return {
            "verdict": "unknown",
            "risk_score": 5,
            "sender_email": "",
            "sender_domain": "",
            "reply_to_domain": reply_to_domain,
            "expected_domain": expected,
            "findings": ["Sender email was not provided"],
            "positives": [],
        }

    if not valid_sender:
        risk_score += 35
        findings.append("Sender email format is invalid or incomplete")
    else:
        positives.append("Sender email format is valid")

    if sender_domain in FREE_EMAIL_DOMAINS:
        risk_score += 35 if expected else 20
        findings.append(f"Sender uses a personal/free email provider: {sender_domain}")

    if expected:
        if _domain_matches(sender_domain, expected):
            positives.append(f"Sender domain matches expected company domain: {expected}")
        else:
            risk_score += 35
            findings.append(
                f"Sender domain '{sender_domain or 'unknown'}' does not match expected company domain '{expected}'"
            )
            if _looks_like_domain(sender_domain, expected):
                risk_score += 30
                findings.append("Sender domain looks visually similar to the expected company domain")

    if reply_to_email:
        if not valid_reply_to:
            risk_score += 20
            findings.append("Reply-To email format is invalid or incomplete")
        elif reply_to_domain and _registrable_domain(reply_to_domain) != _registrable_domain(sender_domain):
            risk_score += 30
            findings.append(f"Reply-To domain '{reply_to_domain}' differs from sender domain '{sender_domain}'")
            if expected and not _domain_matches(reply_to_domain, expected):
                risk_score += 10
                findings.append("Reply-To domain also does not match the expected company domain")
        else:
            positives.append("Reply-To domain aligns with sender domain")

    if sender_domain:
        if any(sender_domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
            risk_score += 15
            findings.append(f"Sender domain uses a suspicious top-level domain: {sender_domain}")
        if "xn--" in sender_domain:
            risk_score += 25
            findings.append("Sender domain uses punycode, which can hide lookalike characters")
        if sender_domain.count(".") >= 3 and not (expected and _domain_matches(sender_domain, expected)):
            risk_score += 8
            findings.append("Sender domain has an unusual number of subdomains")
        if "-" in _root_label(sender_domain) and expected and not _domain_matches(sender_domain, expected):
            risk_score += 8
            findings.append("Sender root domain uses hyphenated branding")

    risk_score = max(0, min(100, risk_score))
    if risk_score >= 60:
        verdict = "suspicious"
    elif risk_score >= 30:
        verdict = "review"
    elif positives:
        verdict = "trusted"
    else:
        verdict = "unknown"

    return {
        "verdict": verdict,
        "risk_score": risk_score,
        "sender_email": sender_address,
        "sender_domain": sender_domain,
        "reply_to_email": reply_to_address,
        "reply_to_domain": reply_to_domain,
        "expected_domain": expected,
        "findings": findings or ["No sender identity issues found"],
        "positives": positives,
    }


def _record_to_text(record: dict | pd.Series) -> str:
    subject = str(record.get("subject", "") or "")
    body = str(record.get("body", "") or "")
    urls = " ".join(_normalize_urls(record.get("urls", "")))
    sender = str(record.get("sender_email", "") or "")
    reply_to = str(record.get("reply_to_email", "") or "")
    expected = str(record.get("expected_domain", "") or "")
    return f"{subject}\n{body}\n{urls}\n{sender}\n{reply_to}\n{expected}".lower()


def _url_flags(url: str) -> dict[str, int | float]:
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    full = url.lower()
    dot_count = host.count(".")

    return {
        "has_ip": int(bool(re.search(r"(\d{1,3}\.){3}\d{1,3}", host))),
        "has_at_symbol": int("@" in full),
        "has_dash_host": int("-" in host),
        "many_subdomains": int(dot_count >= 3),
        "is_shortener": int(host in SHORTENERS),
        "is_https": int(parsed.scheme == "https"),
        "long_url": int(len(full) > 90),
        "suspicious_tld": int(any(host.endswith(tld) for tld in SUSPICIOUS_TLDS)),
        "login_path": int(any(term in path for term in ("login", "verify", "secure", "account"))),
    }


class EmailTextTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "EmailTextTransformer":
        return self

    def transform(self, X: pd.DataFrame) -> list[str]:
        frame = pd.DataFrame(X)
        return [_record_to_text(row) for _, row in frame.iterrows()]


class HeuristicFeatureTransformer(BaseEstimator, TransformerMixin):
    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "HeuristicFeatureTransformer":
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        frame = pd.DataFrame(X)
        features: list[list[float]] = []
        for _, row in frame.iterrows():
            text = _record_to_text(row)
            urls = _normalize_urls(row.get("urls", ""))
            keyword_count = sum(1 for word in PHISHING_KEYWORDS if word in text)
            urgency_count = len(re.findall(r"\b(urgent|immediately|within 24 hours|expire|final notice)\b", text))
            money_count = len(re.findall(r"\b(invoice|payment|refund|bank|wire|payroll|wallet)\b", text))
            credential_count = len(re.findall(r"\b(password|login|credential|mfa|verify|confirm)\b", text))
            punctuation_pressure = text.count("!") + text.count("!!!") * 2

            url_totals = {
                "has_ip": 0,
                "has_at_symbol": 0,
                "has_dash_host": 0,
                "many_subdomains": 0,
                "is_shortener": 0,
                "is_https": 0,
                "long_url": 0,
                "suspicious_tld": 0,
                "login_path": 0,
            }
            for url in urls:
                flags = _url_flags(url)
                for key in url_totals:
                    url_totals[key] += int(flags[key])

            features.append(
                [
                    len(text),
                    len(urls),
                    keyword_count,
                    urgency_count,
                    money_count,
                    credential_count,
                    punctuation_pressure,
                    url_totals["has_ip"],
                    url_totals["has_at_symbol"],
                    url_totals["has_dash_host"],
                    url_totals["many_subdomains"],
                    url_totals["is_shortener"],
                    url_totals["is_https"],
                    url_totals["long_url"],
                    url_totals["suspicious_tld"],
                    url_totals["login_path"],
                ]
            )
        return np.asarray(features, dtype=float)


def build_pipeline() -> Pipeline:
    text_features = Pipeline(
        steps=[
            ("text", EmailTextTransformer()),
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=3500,
                ),
            ),
        ]
    )
    heuristic_features = Pipeline(
        steps=[
            ("heuristics", HeuristicFeatureTransformer()),
            ("scale", StandardScaler()),
        ]
    )
    return Pipeline(
        steps=[
            ("features", FeatureUnion([("text", text_features), ("heuristics", heuristic_features)])),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train_model(dataset_path: Path, model_path: Path) -> dict:
    data = pd.read_csv(dataset_path)
    required = {"subject", "body", "urls", "label"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {', '.join(sorted(missing))}")

    X = data[["subject", "body", "urls"]].fillna("")
    y = data["label"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metrics": {"accuracy": accuracy, "report": report}}, model_path)
    return {"accuracy": round(float(accuracy), 4), "samples": int(len(data)), "model_path": str(model_path)}


def explain_prediction(
    subject: str,
    body: str,
    urls: list[str],
    sender_analysis: dict | None = None,
) -> list[str]:
    text = f"{subject} {body}".lower()
    reasons: list[str] = []

    keyword_text = re.sub(r"\b(no|not|without)\s+urgent\b", " ", text)
    matched = sorted(word for word in PHISHING_KEYWORDS if word in keyword_text)
    if matched:
        reasons.append(f"Suspicious language: {', '.join(matched[:6])}")

    if len(urls) > 2:
        reasons.append(f"Contains multiple URL(s): {len(urls)}")
    for url in urls:
        flags = _url_flags(url)
        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = parsed.netloc.lower()
        if flags["has_ip"]:
            reasons.append(f"URL uses an IP address: {host}")
        if flags["has_at_symbol"]:
            reasons.append("URL contains an @ symbol")
        if flags["many_subdomains"]:
            reasons.append(f"URL has many subdomains: {host}")
        if flags["is_shortener"]:
            reasons.append(f"URL uses a shortener: {host}")
        if flags["suspicious_tld"]:
            reasons.append(f"URL uses a suspicious top-level domain: {host}")
        if not flags["is_https"]:
            reasons.append(f"URL is not HTTPS: {host}")

    if re.search(r"\b(within 24 hours|immediately|final notice|account locked)\b", text):
        reasons.append("Uses urgency or pressure wording")
    if sender_analysis and sender_analysis.get("verdict") in {"review", "suspicious"}:
        reasons.extend(sender_analysis.get("findings", [])[:4])
    if not reasons:
        reasons.append("No strong phishing indicators found")
    return reasons[:8]


@dataclass
class PhishingDetectorService:
    dataset_path: Path
    model_path: Path

    def __post_init__(self) -> None:
        self._model: Pipeline | None = None
        self._metrics: dict = {}

    def is_ready(self) -> bool:
        self._ensure_loaded()
        return self._model is not None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        if not self.model_path.exists():
            train_model(self.dataset_path, self.model_path)
        artifact = joblib.load(self.model_path)
        self._model = artifact["pipeline"]
        self._metrics = artifact.get("metrics", {})

    def predict(
        self,
        subject: str,
        body: str,
        urls: list[str] | None = None,
        sender_email: str | None = None,
        reply_to_email: str | None = None,
        expected_domain: str | None = None,
    ) -> dict:
        self._ensure_loaded()
        assert self._model is not None
        normalized_urls = _normalize_urls(urls)
        sender_analysis = analyze_sender(sender_email, reply_to_email, expected_domain)
        frame = pd.DataFrame(
            [
                {
                    "subject": subject or "",
                    "body": body or "",
                    "urls": " ".join(normalized_urls),
                    "sender_email": sender_email or "",
                    "reply_to_email": reply_to_email or "",
                    "expected_domain": expected_domain or "",
                }
            ]
        )
        probabilities = self._model.predict_proba(frame)[0]
        classes = list(self._model.named_steps["model"].classes_)
        phishing_index = classes.index(1)
        content_probability = float(probabilities[phishing_index])
        sender_probability = sender_analysis["risk_score"] / 100
        phishing_probability = max(content_probability, sender_probability)
        label = "phishing" if phishing_probability >= 0.5 else "legitimate"
        confidence = phishing_probability if label == "phishing" else 1 - phishing_probability
        risk_level = "high" if phishing_probability >= 0.75 else "medium" if phishing_probability >= 0.45 else "low"
        return {
            "label": label,
            "content_probability": round(content_probability, 4),
            "phishing_probability": round(phishing_probability, 4),
            "confidence": round(confidence, 4),
            "risk_level": risk_level,
            "reasons": explain_prediction(subject, body, normalized_urls, sender_analysis),
            "sender_analysis": sender_analysis,
            "model_accuracy": round(float(self._metrics.get("accuracy", 0)), 4),
        }
