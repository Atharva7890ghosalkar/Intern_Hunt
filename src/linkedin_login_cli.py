from __future__ import annotations

from .linkedin_agent import open_login_browser


if __name__ == "__main__":
    print("LinkedIn login browser is opening.")
    print("Log in manually, then return to this console and press Enter.")
    open_login_browser()
    print("LinkedIn session saved.")
