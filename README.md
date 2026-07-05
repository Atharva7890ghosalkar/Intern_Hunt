# LinkedIn Internship Email Draft Agent

This local agent searches LinkedIn posts for target internship opportunities, extracts HR/recruiter email addresses, and creates Gmail drafts using your email template.

It does not send emails. The Gmail integration uses only:

```text
https://www.googleapis.com/auth/gmail.compose
```

## What it does

- Reuses a persistent LinkedIn browser session.
- Searches LinkedIn posts for target roles:
  - AIML intern
  - data science intern
  - machine learning intern
  - python developer intern
- Extracts emails from matching posts.
- Creates Gmail drafts only.
- Saves discovered opportunities and draft status in SQLite.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Gmail setup

1. Create an OAuth desktop client in Google Cloud Console.
2. Enable the Gmail API.
3. Download the OAuth client file as `credentials.json`.
4. Put `credentials.json` in this project root.

The first draft creation will open Google OAuth and create `token.json` locally.

## LinkedIn setup

Run the app:

```powershell
streamlit run app.py
```

Use **Open LinkedIn Login Browser** first. Log into LinkedIn manually. The session is stored in `linkedin_profile/`.

Then use **Search LinkedIn Posts**.

## Email template

Edit:

```text
templates/email_template.txt
```

Available variables:

- `recipient_email`
- `role`
- `company`
- `location`
- `source_url`
- `post_excerpt`

## Safety notes

- The app never calls Gmail send APIs.
- LinkedIn automation is rate-limited and runs in a visible browser.
- If LinkedIn shows captcha or verification, complete it manually in the browser.
