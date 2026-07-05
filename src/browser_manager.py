from __future__ import annotations

from pathlib import Path

from playwright.sync_api import BrowserContext, Page, Playwright

from .config import LINKEDIN_BROWSER_PROFILE_DIR


def launch_browser(playwright: Playwright, user_data_dir: Path = LINKEDIN_BROWSER_PROFILE_DIR) -> BrowserContext:
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        headless=False,
    )


def get_context(playwright: Playwright) -> BrowserContext:
    return launch_browser(playwright)


def get_page(context: BrowserContext) -> Page:
    if context.pages:
        return context.pages[0]
    return context.new_page()


def close_browser(context: BrowserContext) -> None:
    try:
        context.close()
    except Exception:
        pass
