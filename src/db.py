from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .config import DB_PATH


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                query TEXT NOT NULL,
                role TEXT NOT NULL,
                company TEXT,
                location TEXT,
                recipient_email TEXT NOT NULL,
                post_text TEXT NOT NULL,
                source_url TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(recipient_email, role, source_url)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS email_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER NOT NULL,
                recipient_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                gmail_draft_id TEXT,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id)
            )
            """
        )


def save_opportunity(item: dict) -> int | None:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO opportunities (
                platform, query, role, company, location, recipient_email,
                post_text, source_url, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["platform"],
                item["query"],
                item["role"],
                item.get("company"),
                item.get("location"),
                item["recipient_email"],
                item["post_text"],
                item.get("source_url"),
                item["status"],
            ),
        )
        if cur.lastrowid:
            return int(cur.lastrowid)

        existing = conn.execute(
            """
            SELECT id FROM opportunities
            WHERE recipient_email = ? AND role = ? AND source_url IS ?
            """,
            (item["recipient_email"], item["role"], item.get("source_url")),
        ).fetchone()
        return int(existing["id"]) if existing else None


def save_draft(opportunity_id: int, draft: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO email_drafts (
                opportunity_id, recipient_email, subject, body,
                gmail_draft_id, status, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                opportunity_id,
                draft["recipient_email"],
                draft["subject"],
                draft["body"],
                draft.get("gmail_draft_id"),
                draft["status"],
                draft.get("error"),
            ),
        )
        conn.execute(
            "UPDATE opportunities SET status = ? WHERE id = ?",
            (draft["status"], opportunity_id),
        )


def list_opportunities(limit: int = 100) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT *
                FROM opportunities
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )


def list_drafts(limit: int = 100) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return list(
            conn.execute(
                """
                SELECT d.*, o.role, o.company, o.source_url
                FROM email_drafts d
                JOIN opportunities o ON o.id = d.opportunity_id
                ORDER BY d.created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        )
