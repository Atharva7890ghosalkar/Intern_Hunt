from __future__ import annotations

import json
import subprocess
import sys
import traceback
from types import SimpleNamespace

import streamlit as st

from src.config import DATA_DIR, RESUME_PATH, ROOT_DIR, SEARCH_QUERIES, TEMPLATE_PATH
from src.db import init_db, list_drafts, list_opportunities, save_draft, save_opportunity
from src.email_template import build_subject, load_template, render_email_body
from src.gmail_client import create_gmail_draft


ERROR_LOG_PATH = ROOT_DIR / "error.log"


def write_error_log(text: str) -> None:
    ERROR_LOG_PATH.write_text(text, encoding="utf-8")
    print(text, flush=True)


def log_current_exception(exc: BaseException) -> None:
    parts = []
    if isinstance(exc, subprocess.CalledProcessError):
        if exc.stdout:
            parts.append(exc.stdout)
        if exc.stderr:
            parts.append(exc.stderr)
    parts.append(traceback.format_exc())
    write_error_log("\n".join(parts))


def run_linkedin_search(queries: list[str], max_posts: int):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    queries_path = DATA_DIR / "linkedin_queries.json"
    output_path = DATA_DIR / "linkedin_results.json"
    queries_path.write_text(json.dumps(queries), encoding="utf-8")
    if output_path.exists():
        output_path.unlink()

    command = [
        sys.executable,
        "-m",
        "src.linkedin_search_cli",
        "--queries",
        str(queries_path),
        "--output",
        str(output_path),
        "--max-posts",
        str(max_posts),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
        )
    except Exception as exc:
        log_current_exception(exc)
        raise

    rows = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else []
    return [SimpleNamespace(**row) for row in rows]


st.set_page_config(page_title="Internship Draft Agent", layout="wide")
init_db()

st.title("Internship Email Draft Agent")
st.caption("LinkedIn post search -> target-role filter -> HR email extraction -> Gmail draft only.")
st.info(f"Gmail OAuth file expected at credentials.json. Optional resume attachment path: {RESUME_PATH}")

with st.sidebar:
    st.header("Controls")
    st.write("Target roles")
    st.code("AIML intern\nData science intern\nMachine learning intern\nPython developer intern")
    max_posts = st.slider("Max posts per query", min_value=3, max_value=25, value=8)
    create_drafts = st.toggle("Create Gmail drafts after search", value=False)

    if st.button("Open LinkedIn Login Browser", use_container_width=True):
        subprocess.Popen(
            [sys.executable, "-m", "src.linkedin_login_cli"],
            cwd=ROOT_DIR,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )
        st.success("LinkedIn login browser is opening. Log in there, then press Enter in the new console to save the session.")

tab_search, tab_template, tab_gmail, tab_history = st.tabs(["Search", "Email Template", "Gmail Test", "History"])

with tab_search:
    st.subheader("LinkedIn Search")
    queries_text = st.text_area(
        "Search queries",
        value="\n".join(SEARCH_QUERIES),
        height=160,
    )
    queries = [line.strip() for line in queries_text.splitlines() if line.strip()]

    if st.button("Search LinkedIn Posts", type="primary"):
        if not queries:
            st.error("Add at least one search query.")
        else:
            with st.spinner("Searching LinkedIn posts in the visible browser..."):
                results = run_linkedin_search(queries, max_posts)

            if not results:
                st.warning("No matching posts with email addresses were found.")
            elif results:
                st.success(f"Found {len(results)} matching opportunity email(s).")

            for result in results:
                item = {
                    "platform": "LinkedIn",
                    "query": result.query,
                    "role": result.role,
                    "company": result.company,
                    "location": result.location,
                    "recipient_email": result.recipient_email,
                    "post_text": result.post_text,
                    "source_url": result.source_url,
                    "status": "detected",
                }
                opportunity_id = save_opportunity(item)

                context = {
                    "recipient_email": result.recipient_email,
                    "role": result.role,
                    "company": result.company or "",
                    "location": result.location or "",
                    "recruiter_name": "Hiring Team",
                    "title": "",
                    "source_url": result.source_url or "",
                    "post_excerpt": result.post_text[:900],
                }
                subject = build_subject(result.role, result.company)
                body = render_email_body(context)

                with st.expander(f"{result.role} -> {result.recipient_email}", expanded=True):
                    st.write("Company:", result.company or "Not detected")
                    st.write("Location:", result.location or "Not detected")
                    if result.source_url:
                        st.link_button("Open LinkedIn post", result.source_url)
                    st.text_area("Draft preview", body, height=240, key=f"preview_{result.recipient_email}_{result.role}")

                    if create_drafts and opportunity_id:
                        try:
                            attachment = RESUME_PATH if RESUME_PATH.exists() else None
                            draft_id = create_gmail_draft(result.recipient_email, subject, body, attachment)
                            save_draft(
                                opportunity_id,
                                {
                                    "recipient_email": result.recipient_email,
                                    "subject": subject,
                                    "body": body,
                                    "gmail_draft_id": draft_id,
                                    "status": "draft_created",
                                },
                            )
                            st.success(f"Gmail draft created: {draft_id}")
                        except Exception as exc:
                            save_draft(
                                opportunity_id,
                                {
                                    "recipient_email": result.recipient_email,
                                    "subject": subject,
                                    "body": body,
                                    "status": "draft_failed",
                                    "error": str(exc),
                                },
                            )
                            st.error(f"Draft failed: {exc}")

with tab_template:
    st.subheader("Fixed Email Template")
    st.caption(f"Editing file: {TEMPLATE_PATH}")
    template_text = st.text_area("Template", value=load_template(), height=360)
    if st.button("Save Template"):
        TEMPLATE_PATH.write_text(template_text, encoding="utf-8")
        st.success("Template saved.")

with tab_gmail:
    st.subheader("Gmail Draft Test")
    st.caption("Creates one draft addressed to your own email. It does not send anything.")
    test_email = st.text_input("Your Gmail address")
    if st.button("Create Test Draft"):
        if not test_email:
            st.error("Enter your Gmail address first.")
        else:
            body = render_email_body(
                {
                    "recipient_email": test_email,
                    "role": "AI/ML Intern",
                    "company": "Test Company",
                    "location": "",
                    "recruiter_name": "Hiring Team",
                    "title": "",
                    "source_url": "",
                    "post_excerpt": "",
                }
            )
            try:
                attachment = RESUME_PATH if RESUME_PATH.exists() else None
                draft_id = create_gmail_draft(
                    test_email,
                    "Test Draft - Internship Email Draft Agent",
                    body,
                    attachment,
                )
                st.success(f"Test Gmail draft created: {draft_id}")
            except Exception as exc:
                st.error(f"Gmail test failed: {exc}")

with tab_history:
    st.subheader("Detected Opportunities")
    opportunities = list_opportunities()
    st.dataframe([dict(row) for row in opportunities], use_container_width=True)

    st.subheader("Gmail Draft Attempts")
    drafts = list_drafts()
    st.dataframe([dict(row) for row in drafts], use_container_width=True)
