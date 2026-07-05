from __future__ import annotations

import re
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .browser_manager import close_browser, get_context, get_page
from .config import DATA_DIR
from .parsing import parse_post


@dataclass
class LinkedInSearchResult:
    query: str
    role: str
    recipient_email: str
    post_text: str
    source_url: str | None
    company: str | None = None
    location: str | None = None


def open_login_browser() -> None:
    with sync_playwright() as p:
        context = get_context(p)
        page = get_page(context)
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30_000)
        if "login" in page.url.lower():
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30_000)
        input("Log into LinkedIn if needed, then press Enter here to close the browser...")
        close_browser(context)


def search_linkedin_posts(queries: list[str], max_posts_per_query: int = 10, pause_seconds: float = 2.5) -> list[LinkedInSearchResult]:
    results: list[LinkedInSearchResult] = []
    seen_keys: set[tuple[str, str]] = set()

    with sync_playwright() as p:
        context = get_context(p)
        page = get_page(context)
        page.set_default_timeout(5_000)
        page.set_default_navigation_timeout(20_000)

        for query in queries:
            print(f"Searching LinkedIn for: {query}", flush=True)
            url = f"https://www.linkedin.com/search/results/content/?keywords={quote_plus(query)}&origin=GLOBAL_SEARCH_HEADER"
            try:
                page.goto(url, wait_until="commit", timeout=20_000)
            except PlaywrightTimeoutError:
                print("LinkedIn navigation timed out; continuing with the current page state.", flush=True)

            if "login" in page.url.lower():
                close_browser(context)
                raise RuntimeError("LinkedIn session expired.\nPlease login again.")

            _wait_for_linkedin_content(page)

            for _ in range(3):
                try:
                    page.evaluate("window.scrollBy(0, 900)")
                except Exception:
                    pass
                time.sleep(1)

            print("Collecting visible LinkedIn text...", flush=True)
            post_texts = _collect_visible_posts(page, max_posts_per_query)
            _write_debug_snapshot(page, post_texts)
            print(f"Collected {len(post_texts)} visible post candidates.", flush=True)
            for post_text, source_url in post_texts:
                parsed = parse_post(post_text)
                if not parsed:
                    continue

                for email in parsed["emails"]:
                    key = (email, parsed["role"])
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    results.append(
                        LinkedInSearchResult(
                            query=query,
                            role=parsed["role"],
                            recipient_email=email,
                            company=parsed.get("company"),
                            location=parsed.get("location"),
                            post_text=parsed["post_text"],
                            source_url=source_url,
                        )
                    )

            time.sleep(0.5)
            print(f"Finished query: {query}", flush=True)

        close_browser(context)

    return results


def _collect_visible_posts(page, max_posts: int) -> list[tuple[str, str | None]]:
    selectors = [
        "div.feed-shared-update-v2",
        "li.reusable-search__result-container",
        "article",
    ]
    collected: list[tuple[str, str | None]] = []
    body_text = _read_body_text(page)
    collected.extend(_email_centered_chunks(body_text, page.url, max_posts))

    for selector in selectors:
        try:
            locators = page.locator(selector)
            count = min(locators.count(), max_posts)
        except Exception:
            continue

        for index in range(count):
            item = locators.nth(index)
            try:
                text = item.inner_text(timeout=3_000)
                if len(text.strip()) < 40:
                    continue
                url = _extract_post_url(item)
                collected.append((text, url))
            except Exception:
                continue

        if collected:
            return collected[:max_posts]

    chunks = [chunk.strip() for chunk in body_text.split("\n\n") if len(chunk.strip()) > 80]
    return [(chunk, page.url) for chunk in chunks[:max_posts]]


def _wait_for_linkedin_content(page) -> None:
    for _ in range(5):
        text = _read_body_text(page)
        lower = text.lower()
        if "@" in text or "intern" in lower or "posts" in lower:
            return
        time.sleep(1)


def _read_body_text(page) -> str:
    for _ in range(3):
        try:
            text = page.evaluate(
                "() => document.body ? document.body.innerText : document.documentElement.innerText",
                timeout=8_000,
            )
            if text:
                return text
        except Exception:
            time.sleep(1)
    return ""


def _email_centered_chunks(text: str, source_url: str, max_posts: int) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    for match in re.finditer(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", text):
        start = max(0, match.start() - 1200)
        end = min(len(text), match.end() + 1200)
        chunk = text[start:end].strip()
        if chunk and all(chunk != existing for existing, _ in chunks):
            chunks.append((chunk, source_url))
        if len(chunks) >= max_posts:
            break
    return chunks


def _extract_post_url(locator) -> str | None:
    try:
        links = locator.locator("a[href*='/feed/update/'], a[href*='activity']")
        if links.count() == 0:
            return None
        href = links.first.get_attribute("href")
        if href and href.startswith("/"):
            return f"https://www.linkedin.com{href}"
        return href
    except PlaywrightTimeoutError:
        return None


def _write_debug_snapshot(page, post_texts: list[tuple[str, str | None]]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        title = page.title()
        url = page.url
        body_text = _read_body_text(page)
        sample = "\n\n--- POST CANDIDATE ---\n\n".join(text[:2000] for text, _ in post_texts[:3])
        screenshot_path = DATA_DIR / "linkedin_last_screenshot.png"
        try:
            page.screenshot(path=str(screenshot_path), full_page=False)
        except Exception:
            pass
        (DATA_DIR / "linkedin_last_debug.txt").write_text(
            f"TITLE: {title}\nURL: {url}\nBODY_LENGTH: {len(body_text)}\nSCREENSHOT: {screenshot_path}\n\n{sample or body_text[:4000]}",
            encoding="utf-8",
        )
    except Exception:
        pass
