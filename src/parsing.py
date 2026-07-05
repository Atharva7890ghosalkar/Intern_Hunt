from __future__ import annotations

import re

from .config import TARGET_ROLES

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(text: str) -> list[str]:
    found = []
    for email in EMAIL_RE.findall(text):
        normalized = email.strip(".,;:()[]{}<>").lower()
        if normalized not in found:
            found.append(normalized)
    return found


def detect_role(text: str) -> str | None:
    lower = text.lower()
    for role in TARGET_ROLES:
        if role in lower:
            return canonical_role(role)
    return None


def canonical_role(role: str) -> str:
    role = role.lower()
    if role in {"aiml intern", "ai ml intern", "ai/ml intern", "artificial intelligence intern", "ml intern"}:
        return "AI/ML Intern"
    if role in {"data science intern", "data scientist intern"}:
        return "Data Science Intern"
    if role == "machine learning intern":
        return "Machine Learning Intern"
    if role in {"python developer intern", "python intern"}:
        return "Python Developer Intern"
    return role.title()


def detect_location(text: str) -> str | None:
    match = re.search(
        r"(?:location|located at|based in)\s*[:\-]?\s*([A-Za-z ,.-]{2,80}?)(?:\s+(?:email|contact|working|open|interested)\b|$)",
        text,
        re.I,
    )
    if not match:
        return None
    value = match.group(1).strip(" .,-")
    return value[:80] if value else None


def detect_company(text: str) -> str | None:
    patterns = [
        r"(?:at|join)\s+([A-Z][A-Za-z0-9& .'-]{2,50})\s+(?:as|for|team|is|are)",
        r"([A-Z][A-Za-z0-9& .'-]{2,50})\s+is\s+hiring",
        r"we\s+at\s+([A-Z][A-Za-z0-9& .'-]{2,50})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip(" .,-")
    return None


def parse_post(text: str) -> dict | None:
    cleaned = clean_text(text)
    emails = extract_emails(cleaned)
    role = detect_role(cleaned)
    if not emails or not role:
        return None
    return {
        "role": role,
        "emails": emails,
        "company": detect_company(cleaned),
        "location": detect_location(cleaned),
        "post_text": cleaned,
    }
