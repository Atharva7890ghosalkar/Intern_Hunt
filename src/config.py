from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "intern_drafts.db"
BROWSER_PROFILES_DIR = ROOT_DIR / "browser_profiles"
LINKEDIN_BROWSER_PROFILE_DIR = BROWSER_PROFILES_DIR / "linkedin"
TEMPLATE_PATH = ROOT_DIR / "templates" / "email_template.txt"
GMAIL_CREDENTIALS_PATH = ROOT_DIR / "credentials.json"
GMAIL_TOKEN_PATH = ROOT_DIR / "token.json"
RESUME_PATH = DATA_DIR / "resume.pdf"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

TARGET_ROLES = [
    "aiml intern",
    "ai ml intern",
    "ai/ml intern",
    "artificial intelligence intern",
    "machine learning intern",
    "ml intern",
    "data science intern",
    "data scientist intern",
    "python developer intern",
    "python intern",
]

SEARCH_QUERIES = [
    "AI ML intern hiring email",
    "AIML intern hiring email",
    "machine learning intern email",
    "data science intern hiring email",
    "python developer intern internship email",
    "internship send resume AI ML",
]
