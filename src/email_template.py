from __future__ import annotations

from jinja2 import Template

from .config import TEMPLATE_PATH


LEGACY_PLACEHOLDERS = {
    "{RECRUITER_NAME}": "{{ recruiter_name }}",
    "{TITLE}": "{{ title }}",
    "{ROLE_NAME}": "{{ role }}",
    "{COMPANY_NAME}": "{{ company }}",
    "{LOCATION}": "{{ location }}",
    "{EMAIL}": "{{ recipient_email }}",
}


def load_template() -> str:
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not TEMPLATE_PATH.exists():
        TEMPLATE_PATH.write_text("", encoding="utf-8")
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def render_email_body(context: dict) -> str:
    template_text = load_template()
    for old, new in LEGACY_PLACEHOLDERS.items():
        template_text = template_text.replace(old, new)
    rendered = Template(template_text).render(**context)
    return rendered.replace("  ", " ").replace(" ,", ",")


def build_subject(role: str, company: str | None = None) -> str:
    if company:
        return f"Application for {role} - {company}"
    return f"Application for {role}"
