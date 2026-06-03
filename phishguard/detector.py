from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from email.utils import parseaddr
from html.parser import HTMLParser
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
RISKY_ATTACHMENT_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".docm",
    ".exe",
    ".hta",
    ".html",
    ".htm",
    ".img",
    ".iso",
    ".js",
    ".lnk",
    ".ps1",
    ".rar",
    ".scr",
    ".vbs",
    ".xlsm",
    ".zip",
}
TRACKING_IMAGE_HINTS = ("pixel", "track", "tracking", "beacon", "open")
MODEL_VERSION = 2
FEATURE_COLUMNS = [
    "subject",
    "body",
    "urls",
    "html_body",
    "image_urls",
    "attachment_names",
    "sender_email",
    "reply_to_email",
    "expected_domain",
]
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
    if isinstance(urls, float) and pd.isna(urls):
        return []
    if isinstance(urls, str):
        pieces = re.split(r"[\s,]+", urls)
        return [piece.strip() for piece in pieces if piece.strip()]
    return [str(url).strip() for url in urls if str(url).strip()]


def _normalize_attachment_names(attachments: str | Iterable[str] | None) -> list[str]:
    if attachments is None:
        return []
    if isinstance(attachments, float) and pd.isna(attachments):
        return []
    if isinstance(attachments, str):
        pieces = re.split(r"[\n,;]+", attachments)
        return [piece.strip() for piece in pieces if piece.strip()]
    return [str(item).strip() for item in attachments if str(item).strip()]


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen.add(key)
            items.append(value.strip())
    return items


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


class EmailHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.form_count = 0
        self.form_field_count = 0
        self.script_count = 0
        self.hidden_count = 0
        self._link_stack: list[dict[str, list[str] | str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {name.lower(): value or "" for name, value in attrs}
        style = attr_map.get("style", "").replace(" ", "").lower()
        if any(marker in style for marker in ("display:none", "visibility:hidden", "opacity:0")):
            self.hidden_count += 1

        if tag == "a" and attr_map.get("href"):
            self._link_stack.append({"href": attr_map["href"], "text_parts": []})
        elif tag == "img":
            self.images.append(
                {
                    "src": attr_map.get("src", ""),
                    "alt": attr_map.get("alt", ""),
                    "width": attr_map.get("width", ""),
                    "height": attr_map.get("height", ""),
                }
            )
        elif tag == "form":
            self.form_count += 1
        elif tag in {"input", "select", "textarea", "button"}:
            self.form_field_count += 1
        elif tag == "script":
            self.script_count += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._link_stack:
            link = self._link_stack.pop()
            text_parts = link.get("text_parts", [])
            text = " ".join(str(part).strip() for part in text_parts if str(part).strip())
            self.links.append({"href": str(link.get("href", "")), "text": text})

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        self.text_parts.append(text)
        if self._link_stack:
            text_parts = self._link_stack[-1].setdefault("text_parts", [])
            if isinstance(text_parts, list):
                text_parts.append(text)


def _empty_html_summary() -> dict:
    return {
        "text": "",
        "links": [],
        "images": [],
        "form_count": 0,
        "form_field_count": 0,
        "script_count": 0,
        "hidden_count": 0,
    }


def _summarize_html(html_body: str | None) -> dict:
    if not html_body:
        return _empty_html_summary()
    parser = EmailHTMLParser()
    try:
        parser.feed(str(html_body))
        parser.close()
    except Exception:
        return _empty_html_summary()
    return {
        "text": " ".join(parser.text_parts),
        "links": parser.links,
        "images": parser.images,
        "form_count": parser.form_count,
        "form_field_count": parser.form_field_count,
        "script_count": parser.script_count,
        "hidden_count": parser.hidden_count,
    }


def _html_urls(summary: dict) -> list[str]:
    urls = []
    for link in summary.get("links", []):
        href = str(link.get("href", "")).strip()
        if href and not href.startswith(("#", "mailto:", "tel:")):
            urls.append(href)
    return _normalize_urls(urls)


def _html_image_urls(summary: dict) -> list[str]:
    return _normalize_urls(image.get("src", "") for image in summary.get("images", []))


def _host_from_url_like_text(value: str) -> str:
    match = re.search(r"(https?://[^\s<>'\"]+|www\.[^\s<>'\"]+|[a-z0-9.-]+\.[a-z]{2,})", value.lower())
    if not match:
        return ""
    candidate = match.group(1)
    parsed = urlparse(candidate if "://" in candidate else f"http://{candidate}")
    return _normalize_domain(parsed.netloc)


def _mismatched_html_links(summary: dict) -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    for link in summary.get("links", []):
        href = str(link.get("href", ""))
        text = str(link.get("text", ""))
        href_host = _normalize_domain(urlparse(href if "://" in href else f"http://{href}").netloc)
        text_host = _host_from_url_like_text(text)
        if href_host and text_host and _registrable_domain(href_host) != _registrable_domain(text_host):
            mismatches.append({"text_host": text_host, "href_host": href_host, "text": text, "href": href})
    return mismatches


def _image_dimension(value: str) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None


def _looks_like_tracking_image(image: dict[str, str]) -> bool:
    src = str(image.get("src", "")).lower()
    width = _image_dimension(str(image.get("width", "")))
    height = _image_dimension(str(image.get("height", "")))
    return any(hint in src for hint in TRACKING_IMAGE_HINTS) or (
        width is not None and height is not None and width <= 2 and height <= 2
    )


def _risky_attachment_extension(name: str) -> str:
    return Path(name.lower()).suffix


def _has_double_extension(name: str) -> bool:
    parts = [part for part in Path(name.lower()).name.split(".") if part]
    return len(parts) >= 3 and f".{parts[-1]}" in RISKY_ATTACHMENT_EXTENSIONS


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
    html_summary = _summarize_html(str(record.get("html_body", "") or ""))
    html_text = str(html_summary.get("text", ""))
    html_link_text = " ".join(
        f"{link.get('text', '')} {link.get('href', '')}" for link in html_summary.get("links", [])
    )
    html_images = " ".join(
        f"{image.get('alt', '')} {image.get('src', '')}" for image in html_summary.get("images", [])
    )
    urls = " ".join(_normalize_urls(record.get("urls", "")))
    image_urls = " ".join(_normalize_urls(record.get("image_urls", "")))
    attachments = " ".join(_normalize_attachment_names(record.get("attachment_names", "")))
    sender = str(record.get("sender_email", "") or "")
    reply_to = str(record.get("reply_to_email", "") or "")
    expected = str(record.get("expected_domain", "") or "")
    return (
        f"{subject}\n{body}\n{html_text}\n{html_link_text}\n{urls}\n{html_images}\n"
        f"{image_urls}\n{attachments}\n{sender}\n{reply_to}\n{expected}"
    ).lower()


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
            html_summary = _summarize_html(str(row.get("html_body", "") or ""))
            urls = _dedupe(_normalize_urls(row.get("urls", "")) + _html_urls(html_summary))
            image_urls = _dedupe(_normalize_urls(row.get("image_urls", "")) + _html_image_urls(html_summary))
            attachments = _normalize_attachment_names(row.get("attachment_names", ""))
            keyword_count = sum(1 for word in PHISHING_KEYWORDS if word in text)
            urgency_count = len(re.findall(r"\b(urgent|immediately|within 24 hours|expire|final notice)\b", text))
            money_count = len(re.findall(r"\b(invoice|payment|refund|bank|wire|payroll|wallet)\b", text))
            credential_count = len(re.findall(r"\b(password|login|credential|mfa|verify|confirm)\b", text))
            punctuation_pressure = text.count("!") + text.count("!!!") * 2
            mismatched_links = _mismatched_html_links(html_summary)
            tracking_images = sum(1 for image in html_summary.get("images", []) if _looks_like_tracking_image(image))
            tracking_images += sum(
                1 for url in image_urls if any(hint in url.lower() for hint in TRACKING_IMAGE_HINTS)
            )
            remote_images = sum(
                1
                for url in image_urls
                if urlparse(url if "://" in url else f"http://{url}").scheme in {"http", "https"}
            )
            risky_attachments = sum(
                1 for name in attachments if _risky_attachment_extension(name) in RISKY_ATTACHMENT_EXTENSIONS
            )
            double_extensions = sum(1 for name in attachments if _has_double_extension(name))
            image_heavy = int((len(image_urls) >= 2 or tracking_images > 0) and len(text) < 500)

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
                    int(bool(str(row.get("html_body", "") or "").strip())),
                    len(html_summary.get("links", [])),
                    len(mismatched_links),
                    len(image_urls),
                    remote_images,
                    tracking_images,
                    int(html_summary.get("form_count", 0)),
                    int(html_summary.get("form_field_count", 0)),
                    int(html_summary.get("script_count", 0)),
                    int(html_summary.get("hidden_count", 0)),
                    risky_attachments,
                    double_extensions,
                    image_heavy,
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

    for column in FEATURE_COLUMNS:
        if column not in data.columns:
            data[column] = ""
    X = data[FEATURE_COLUMNS].fillna("")
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
    joblib.dump(
        {"version": MODEL_VERSION, "pipeline": pipeline, "metrics": {"accuracy": accuracy, "report": report}},
        model_path,
    )
    return {"accuracy": round(float(accuracy), 4), "samples": int(len(data)), "model_path": str(model_path)}


def analyze_email_structure(
    html_body: str | None = None,
    urls: list[str] | None = None,
    image_urls: list[str] | None = None,
    attachment_names: list[str] | None = None,
) -> dict:
    html_summary = _summarize_html(html_body)
    normalized_urls = _dedupe(_normalize_urls(urls) + _html_urls(html_summary))
    normalized_images = _dedupe(_normalize_urls(image_urls) + _html_image_urls(html_summary))
    attachments = _normalize_attachment_names(attachment_names)
    findings: list[str] = []
    positives: list[str] = []
    risk_score = 0

    if html_body:
        positives.append("HTML body was parsed for links, images, forms, and hidden content")

    mismatched_links = _mismatched_html_links(html_summary)
    for mismatch in mismatched_links[:3]:
        risk_score += 30
        findings.append(
            f"HTML link text shows '{mismatch['text_host']}' but opens '{mismatch['href_host']}'"
        )

    if html_summary.get("form_count") or html_summary.get("form_field_count"):
        risk_score += 35
        findings.append("HTML email contains form fields, which can be used to collect credentials")
    if html_summary.get("script_count"):
        risk_score += 35
        findings.append("HTML email contains script content")
    if html_summary.get("hidden_count"):
        risk_score += 20
        findings.append("HTML email contains hidden or invisible content")

    tracking_images = [
        image for image in html_summary.get("images", []) if _looks_like_tracking_image(image)
    ]
    tracking_images += [
        {"src": url, "alt": ""}
        for url in normalized_images
        if any(hint in url.lower() for hint in TRACKING_IMAGE_HINTS)
    ]
    if tracking_images:
        risk_score += min(25, 12 + len(tracking_images) * 4)
        findings.append("Email includes image patterns commonly used for open tracking")

    if len(normalized_images) >= 3:
        risk_score += 8
        findings.append(f"Email references multiple remote image(s): {len(normalized_images)}")

    if normalized_images and not (html_summary.get("text") or "").strip():
        risk_score += 12
        findings.append("Email is image-heavy with little visible text")

    for url in normalized_urls:
        flags = _url_flags(url)
        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = parsed.netloc.lower()
        if flags["has_ip"]:
            risk_score += 25
            findings.append(f"Clickable URL uses an IP address: {host}")
        if flags["has_at_symbol"]:
            risk_score += 20
            findings.append("Clickable URL contains an @ symbol")
        if flags["is_shortener"]:
            risk_score += 20
            findings.append(f"Clickable URL uses a shortener: {host}")
        if flags["suspicious_tld"]:
            risk_score += 15
            findings.append(f"Clickable URL uses a suspicious top-level domain: {host}")
        if flags["many_subdomains"]:
            risk_score += 8
            findings.append(f"Clickable URL has many subdomains: {host}")
        if flags["login_path"]:
            risk_score += 8
            findings.append(f"Clickable URL path asks for account access: {host}")
        if not flags["is_https"]:
            risk_score += 5
            findings.append(f"Clickable URL is not HTTPS: {host}")

    for name in attachments:
        extension = _risky_attachment_extension(name)
        if extension in RISKY_ATTACHMENT_EXTENSIONS:
            risk_score += 35
            findings.append(f"Attachment has a risky file type: {name}")
        if _has_double_extension(name):
            risk_score += 25
            findings.append(f"Attachment appears to use a double extension: {name}")

    risk_score = max(0, min(100, risk_score))
    if risk_score >= 60:
        verdict = "suspicious"
    elif risk_score >= 30:
        verdict = "review"
    else:
        verdict = "low"

    if not findings:
        findings.append("No high-risk HTML, link, image, or attachment indicators found")

    return {
        "verdict": verdict,
        "risk_score": risk_score,
        "link_count": len(normalized_urls),
        "image_count": len(normalized_images),
        "attachment_count": len(attachments),
        "findings": _dedupe(findings)[:10],
        "positives": positives,
    }


def explain_prediction(
    subject: str,
    body: str,
    urls: list[str],
    sender_analysis: dict | None = None,
    html_body: str | None = None,
    image_urls: list[str] | None = None,
    attachment_names: list[str] | None = None,
    structure_analysis: dict | None = None,
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
    if structure_analysis is None and (html_body or image_urls or attachment_names):
        structure_analysis = analyze_email_structure(html_body, urls, image_urls, attachment_names)
    if structure_analysis and structure_analysis.get("verdict") in {"review", "suspicious"}:
        reasons.extend(structure_analysis.get("findings", [])[:4])
    if not reasons:
        reasons.append("No strong phishing indicators found")
    return _dedupe(reasons)[:10]


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
        if artifact.get("version") != MODEL_VERSION:
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
        html_body: str | None = None,
        image_urls: list[str] | None = None,
        attachment_names: list[str] | None = None,
    ) -> dict:
        self._ensure_loaded()
        assert self._model is not None
        html_summary = _summarize_html(html_body)
        normalized_urls = _dedupe(_normalize_urls(urls) + _html_urls(html_summary))
        normalized_images = _dedupe(_normalize_urls(image_urls) + _html_image_urls(html_summary))
        normalized_attachments = _normalize_attachment_names(attachment_names)
        sender_analysis = analyze_sender(sender_email, reply_to_email, expected_domain)
        structure_analysis = analyze_email_structure(
            html_body=html_body,
            urls=normalized_urls,
            image_urls=normalized_images,
            attachment_names=normalized_attachments,
        )
        frame = pd.DataFrame(
            [
                {
                    "subject": subject or "",
                    "body": body or "",
                    "urls": " ".join(normalized_urls),
                    "html_body": html_body or "",
                    "image_urls": " ".join(normalized_images),
                    "attachment_names": " ".join(normalized_attachments),
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
        structure_probability = structure_analysis["risk_score"] / 100
        phishing_probability = max(content_probability, sender_probability, structure_probability)
        label = "phishing" if phishing_probability >= 0.5 else "legitimate"
        confidence = phishing_probability if label == "phishing" else 1 - phishing_probability
        risk_level = "high" if phishing_probability >= 0.75 else "medium" if phishing_probability >= 0.45 else "low"
        return {
            "label": label,
            "content_probability": round(content_probability, 4),
            "structure_probability": round(structure_probability, 4),
            "phishing_probability": round(phishing_probability, 4),
            "confidence": round(confidence, 4),
            "risk_level": risk_level,
            "reasons": explain_prediction(
                subject,
                body,
                normalized_urls,
                sender_analysis,
                html_body=html_body,
                image_urls=normalized_images,
                attachment_names=normalized_attachments,
                structure_analysis=structure_analysis,
            ),
            "sender_analysis": sender_analysis,
            "structure_analysis": structure_analysis,
            "model_accuracy": round(float(self._metrics.get("accuracy", 0)), 4),
        }
