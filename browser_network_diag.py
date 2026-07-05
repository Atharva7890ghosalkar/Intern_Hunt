from playwright.sync_api import sync_playwright
import traceback


URLS = [
    "https://example.com/",
    "https://www.google.com/",
    "https://www.linkedin.com/",
]


def main() -> None:
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="browser_profiles/network_diag",
            headless=False,
        )
        try:
            page = context.new_page()
            print("browser.version:", context.browser.version if context.browser else "unknown")

            for url in URLS:
                print(f"\nURL: {url}")
                try:
                    page.goto(url, wait_until="commit", timeout=30_000)
                    print("SUCCESS")
                except Exception as exc:
                    print("FAILED")
                    print("Full exception:")
                    traceback.print_exception(type(exc), exc, exc.__traceback__)
                finally:
                    print("page.url:", page.url)
                    print("context.cookies():", context.cookies())
        finally:
            context.close()


if __name__ == "__main__":
    main()
