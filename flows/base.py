"""Base class for agent flows: session loading, messaging, and deletion dispatch."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from didr import config


class PlatformFlow:
    platform: str = ""

    HAS_MEMORY_UI: bool = True

    ERASURE_DISPATCH: dict[str, str] = {}

    MEMORY_FIELD_INJECTION_TYPES: set[str] = {"I3"}

    EXTRA_LAUNCH_ARGS: list[str] = []
    # Launch flags to drop. Gemini answers every message with an error when Chrome
    # carries the "--enable-automation" flag (seen in our November 2026 test run).
    IGNORE_DEFAULT_ARGS: list[str] = []

    # ChatGPT, Claude, Copilot, and Perplexity show a bot check (e.g. Cloudflare's
    # "Just a moment...") to any browser driven by Playwright, even with a valid
    # login. playwright-stealth hides the automation signals so the pipeline can
    # run on your own logged-in account, as in the study. Off by default.
    USE_STEALTH: bool = False

    def _apply_stealth(self, context) -> None:
        if self.USE_STEALTH:
            Stealth().apply_stealth_sync(context)

    def __init__(self, headless: bool | None = None, session_label: str | None = None, playwright=None):
        session = config.session_path(self.platform, session_label)
        if not session.exists():
            label_hint = f" --label {session_label}" if session_label else ""
            raise FileNotFoundError(
                f"No saved session for {self.platform!r}"
                f"{f' (label {session_label!r})' if session_label else ''}: follow docs/sessions.md, "
                f"then run `python scripts/import_cookies.py {self.platform}{label_hint.replace('--label', '--account')}`."
            )
        self._session_path = session
        self._headless = config.HEADLESS if headless is None else headless
        self._playwright = playwright
        self._owns_playwright = playwright is None
        self._browser = None
        self._context = None
        self.page = None
        self.memory_shot_path: Path | None = None

    def __enter__(self):
        try:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self._headless, channel="chrome",
                args=self.EXTRA_LAUNCH_ARGS or None,
                ignore_default_args=self.IGNORE_DEFAULT_ARGS or None,
            )
            self._context = self._browser.new_context(storage_state=str(self._session_path))
            self._apply_stealth(self._context)
            self._prepare_context(self._context)
            self.page = self._context.new_page()
            self.page.goto(config.PLATFORMS[self.platform], wait_until="domcontentloaded")
            self.page.wait_for_timeout(2500)
            self._verify_logged_in()
        except Exception:
            if self._browser:
                self._browser.close()
            if self._playwright and self._owns_playwright:
                self._playwright.stop()
            raise
        return self

    def _prepare_context(self, context) -> None:
        pass

    SIGN_IN_URL_MARKERS: tuple[str, ...] = ("/sign_in", "/signin", "/login", "/log-in", "/auth/login")

    def _raise_if_signed_out(self) -> None:
        url = self.page.url.lower()
        if any(marker in url for marker in self.SIGN_IN_URL_MARKERS):
            raise RuntimeError(
                f"{self.platform} session is logged out (redirected to {self.page.url.split('?')[0]}). "
                f"Export the cookies again and rerun `python scripts/import_cookies.py {self.platform}` (docs/sessions.md)."
            )

    def _verify_logged_in(self) -> None:
        self._raise_if_signed_out()

    NON_ANSWER_SUBSTRINGS: tuple[str, ...] = (
        "having trouble responding",
        "try again in a bit",
        "try this again in a bit",
        "upgrade to keep chatting",
        "message limit",
        "session limit",
        "rate limit",
        "too many requests",
        "you've reached your limit",
        "hit your",
        "high demand",
        "over capacity",
        "at capacity",
        "something went wrong",
    )

    def assert_real_answer(self, reply: str) -> None:
        text = (reply or "").strip()
        if not text:
            raise RuntimeError("assert_real_answer: no reply text captured -- not a real answer")
        lower = text.lower()
        hit = next((s for s in self.NON_ANSWER_SUBSTRINGS if s in lower), None)
        if hit:
            raise RuntimeError(f"assert_real_answer: reply looks like a non-answer (matched {hit!r}), not a real answer: {text[:200]!r}")

    def __exit__(self, *exc):
        if self._browser:
            self._browser.close()
        if self._playwright and self._owns_playwright:
            self._playwright.stop()

    def _scroll_to_bottom(self, element=None) -> None:
        if element:
            self.page.evaluate("el => el.scrollTo(0, el.scrollHeight)", element)
        else:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.page.wait_for_timeout(1500)


    def new_conversation(self) -> None:
        raise NotImplementedError

    def open_conversation(self, ref: str) -> None:
        self.page.goto(ref, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        self._raise_if_signed_out()
        last_reply = getattr(self, "_last_reply_text", None)
        if last_reply is None:
            self.page.wait_for_timeout(5000)
            return
        prev, stable = None, 0
        for _ in range(30):
            self.page.wait_for_timeout(1000)
            cur = last_reply()
            stable = stable + 1 if cur and cur == prev else 0
            if stable >= 2:
                return
            prev = cur
        raise RuntimeError(f"open_conversation: earlier replies never finished loading at {ref}")

    def send_message(self, text: str) -> str:
        raise NotImplementedError

    def set_memory_field(self, text: str) -> str | None:
        raise NotImplementedError

    def upload_file(self, file_path: str, caption: str | None = None) -> str:
        raise NotImplementedError

    def erase_via_ui(
        self,
        erasure_desc: str,
        token: str,
        injection_text: str,
        ref: str | None = None,
        erasure_request_text: str | None = None,
    ) -> None:
        method_name = self.ERASURE_DISPATCH.get(erasure_desc)
        if method_name is None:
            raise NotImplementedError(
                f"{type(self).__name__} has no ERASURE_DISPATCH entry for "
                f"{erasure_desc!r}. Known: {list(self.ERASURE_DISPATCH)}"
            )
        kwargs = {"token": token, "injection_text": injection_text, "ref": ref}
        if erasure_request_text is not None:
            kwargs["erasure_request_text"] = erasure_request_text
        getattr(self, method_name)(**kwargs)

    def _find_conversation_by_token(self, token: str, base_url: str, link_selector: str) -> str | None:
        links = self.page.query_selector_all(link_selector)
        hrefs = [link.get_attribute("href") for link in links]
        for href in hrefs:
            if not href:
                continue
            self.page.goto(f"{base_url}{href}" if href.startswith("/") else href)
            self.page.wait_for_timeout(1200)
            if token.strip().lower() in self.page.inner_text("body").lower():
                return self.page.url
        return None

    def read_memory_settings(self) -> str:
        if not self.HAS_MEMORY_UI:
            return "N/A"
        raise NotImplementedError
