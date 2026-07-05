from __future__ import annotations

import base64
import mimetypes
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES, GMAIL_TOKEN_PATH


def get_gmail_service():
    if not GMAIL_CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "Missing credentials.json. Create a Gmail OAuth desktop client, "
            "enable Gmail API, and place credentials.json in the project root."
        )

    creds = None
    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(GMAIL_CREDENTIALS_PATH), GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        GMAIL_TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def create_gmail_draft(recipient: str, subject: str, body: str, attachment_path: Path | None = None) -> str:
    message = _build_message(recipient, subject, body, attachment_path)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    service = get_gmail_service()
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return str(draft["id"])


def _build_message(recipient: str, subject: str, body: str, attachment_path: Path | None):
    if not attachment_path or not attachment_path.exists():
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = recipient
        message["subject"] = subject
        return message

    message = MIMEMultipart()
    message["to"] = recipient
    message["subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))

    content_type, _ = mimetypes.guess_type(str(attachment_path))
    main_type, sub_type = (content_type or "application/octet-stream").split("/", 1)
    with attachment_path.open("rb") as file_obj:
        part = MIMEBase(main_type, sub_type)
        part.set_payload(file_obj.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=attachment_path.name)
    message.attach(part)
    return message
