"""AgentBay API client using official SDK.

This module provides a client wrapper around the official AgentBay SDK
for browser and code execution operations.

# MOIRIA: Fork-specific — multi-region AgentBay support with custom timeout handling.
#   Not present in upstream v1.8.1.

Supports multiple regions:
- china: https://agentbay.wuying.aliyuncs.com/v2 (default)
- intl/singapore: https://agentbay-intl.wuying.aliyuncs.com/v2
"""

import asyncio
import os
import uuid
import base64
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from agentbay import AgentBay, BrowserOption, BrowserProxy, CreateSessionParams
from playwright.async_api import async_playwright, Page as PWPage, Browser as PWBrowser, BrowserContext as PWBrowserContext


# Region endpoint configuration
# These are Alibaba Cloud RPC endpoints used by the AgentBay SDK for session creation.
# The SSE streaming endpoint (agentbay-intl.wuying.aliyuncs.com/v2/sse) is separate
# and handled internally by the SDK.
AGENTBAY_ENDPOINTS = {
    'china': 'wuyingai.cn-shanghai.aliyuncs.com',
    'cn': 'wuyingai.cn-shanghai.aliyuncs.com',
    'intl': 'wuyingai.ap-southeast-1.aliyuncs.com',
    'singapore': 'wuyingai.ap-southeast-1.aliyuncs.com',
    'sg': 'wuyingai.ap-southeast-1.aliyuncs.com',
}


@dataclass
class AgentBaySession:
    """AgentBay session info."""
    session_id: str
    image: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class AgentBayClient:
    """Client for AgentBay SDK interactions."""

    def __init__(self, api_key: str, region: str = 'intl'):
        """Initialize AgentBay client.
        
        Args:
            api_key: AgentBay API key (ako-...)
            region: Region endpoint ('china', 'intl', 'singapore', 'sg')
                   Default: 'intl' (Singapore international endpoint)
        """
        self.api_key = api_key
        self.region = region.lower()
        self.endpoint = AGENTBAY_ENDPOINTS.get(self.region, AGENTBAY_ENDPOINTS['intl'])
        
        logger.info(f"[AgentBay] Initializing client with region={self.region}, endpoint={self.endpoint}")
        
        self._sdk = AgentBay(api_key=api_key)
        
        # Override SDK endpoint: the SDK defaults to cn-shanghai (China) but intl keys
        # require ap-southeast-1. We must set the endpoint on the internal client directly.
        self._sdk.client._endpoint = self.endpoint
        logger.info(f"[AgentBay] SDK endpoint overridden to: {self.endpoint}")
        
        self._session = None
        self._image_type = None
        
        # Playwright CDP connection (for fast browser operations)
        self._cdp_browser: Optional[PWBrowser] = None
        self._cdp_context: Optional[PWBrowserContext] = None
        self._cdp_page: Optional[PWPage] = None
        self._playwright = None

    async def create_session(self, image: str = "linux_latest") -> AgentBaySession:
        """Create a new session using SDK.

        Closes any existing session first to prevent leaked sessions
        on the AgentBay API side.
        """
        # Close existing session to prevent leaking concurrent sessions
        if self._session:
            logger.info("[AgentBay] Closing existing session before creating new one")
            await self.close_session()

        image_id_map = {
            "browser_latest": "browser_latest",
            "code_latest": "linux_latest",
            "linux_latest": "linux_latest",
            "windows_latest": "windows_latest",
        }
        image_id = image_id_map.get(image, image)
        self._image_type = image

        result = await asyncio.to_thread(self._sdk.create, CreateSessionParams(image_id=image_id))
        if not result.success:
            raise RuntimeError(f"Failed to create session: {result.error_message}")

        self._session = result.session
        self._browser_initialized = False
        logger.info(f"[AgentBay] Created session with image {image_id}")
        return AgentBaySession(
            session_id=self._session.session_id,
            image=image,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )

    async def close_session(self):
        """Release the current session + CDP connection."""
        await self.close_cdp_connection()
        if not self._session:
            return
        try:
            await asyncio.to_thread(self._session.delete)
            logger.info(f"[AgentBay] Closed session")
        except Exception as e:
            logger.warning(f"[AgentBay] Failed to close session: {e}")
        finally:
            self._session = None
            self._browser_initialized = False

    # ─── CDP / Playwright Connection ─────────────────────────

    async def _ensure_cdp_connection(self):
        """Connect Playwright to the AgentBay browser via CDP."""
        if self._cdp_browser and self._cdp_browser.is_connected():
            return  # Already connected

        endpoint_url = self._session.browser.get_endpoint_url()
        logger.info(f"[AgentBay] CDP endpoint: {endpoint_url[:60]}...")

        self._playwright = await async_playwright().start()
        self._cdp_browser = await self._playwright.chromium.connect_over_cdp(endpoint_url)
        contexts = self._cdp_browser.contexts

        # Create or reuse context. If creating fresh, set locale/timezone at the
        # browser-engine level — this is the strongest geo signal. If reusing an
        # existing SDK-created context, we can't change locale but we still inject
        # headers + navigator overrides to push sites toward Canadian content.
        if contexts:
            self._cdp_context = contexts[0]
            logger.info(f"[AgentBay] Reusing existing SDK context")
        else:
            self._cdp_context = await self._cdp_browser.new_context(
                locale="fr-CA",
                timezone_id="America/Toronto",
            )
            logger.info(f"[AgentBay] Created fresh context (fr-CA, America/Toronto)")

        # Use _find_or_create_page to find existing pages with content,
        # not create a new blank page. This function also adds init scripts.
        await self._find_or_create_page()

        # Inject Accept-Language header on every request — sites that ignore
        # navigator.language often still respect this header.
        await self._cdp_context.set_extra_http_headers({
            "Accept-Language": "fr-CA,fr;q=0.9,en-CA;q=0.8,en;q=0.7",
        })

        # Spoof navigator.language / navigator.languages for JS-based detection.
        # Init scripts on the context apply to ALL future pages (not just this one).
        await self._cdp_context.add_init_script("""
            Object.defineProperty(navigator, 'language', { get: () => 'fr-CA' });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-CA', 'fr', 'en-CA', 'en'],
            });
        """)

        logger.info(f"[AgentBay] CDP connected successfully (fr-CA locale, America/Toronto TZ)")

    async def _find_or_create_page(self):
        """Find an existing non-blank page in ANY context, or create one.

        The AgentBay SDK may have already created pages (the ones the agent
        navigated to) in a context we didn't create. We must scan ALL browser
        contexts to find them, otherwise we always get a blank new page and
        screenshots are always white.
        """
        if self._cdp_browser:
            # Scan ALL contexts, not just our own
            for ctx in self._cdp_browser.contexts:
                existing_pages = ctx.pages
                for p in existing_pages:
                    try:
                        url = p.url
                        if url and url != "about:blank":
                            logger.info(
                                f"[AgentBay] Found existing page across contexts: {url[:80]}"
                            )
                            self._cdp_context = ctx
                            self._cdp_page = p
                            # Layer our locale overrides on top
                            await self._cdp_page.add_init_script("""
                                Object.defineProperty(navigator, 'language', { get: () => 'fr-CA' });
                                Object.defineProperty(navigator, 'languages', {
                                    get: () => ['fr-CA', 'fr', 'en-CA', 'en'],
                                });
                            """)
                            return p
                    except Exception:
                        continue

            # No non-blank pages found anywhere — use the last page in any context
            for ctx in self._cdp_browser.contexts:
                if ctx.pages:
                    self._cdp_context = ctx
                    self._cdp_page = ctx.pages[-1]
                    logger.info(f"[AgentBay] Using last page in context (blank, may load later)")
                    return self._cdp_page

        # Absolutely no pages anywhere — create a new one in our context
        self._cdp_page = await self._cdp_context.new_page()
        await self._cdp_page.add_init_script("""
            Object.defineProperty(navigator, 'language', { get: () => 'fr-CA' });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-CA', 'fr', 'en-CA', 'en'],
            });
        """)
        logger.info(f"[AgentBay] Created new page (no existing pages anywhere)")
        return self._cdp_page

    async def get_cdp_page(self) -> PWPage:
        """Return a Playwright page — prefers existing pages with content."""
        if not self._session or self._image_type not in ("browser", "browser_latest"):
            await self.create_session("browser_latest")

        await self._ensure_browser_initialized()
        await self._ensure_cdp_connection()
        return await self._find_or_create_page()

    async def close_cdp_connection(self):
        """Close the CDP connection cleanly."""
        # Reset init scripts (they persist across page reloads but not across
        # context recreation — good to clear explicitly)
        if self._cdp_page:
            try:
                await self._cdp_page.close()
            except Exception:
                pass
        if self._cdp_context:
            try:
                await self._cdp_context.close()
            except Exception:
                pass
        if self._cdp_browser:
            try:
                await self._cdp_browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
        self._cdp_browser = None
        self._cdp_context = None
        self._cdp_page = None
        self._playwright = None

    # ─── Browser Operations ──────────────────────────

    async def _ensure_browser_initialized(self):
        """Ensure the browser is initialized for the current session."""
        if not self._session:
            raise RuntimeError("No active browser session")
        if not getattr(self, "_browser_initialized", False):
            from agentbay import BrowserOption, BrowserFingerprint
            from agentbay._common.models.browser import BrowserViewport, BrowserScreen
            
            # Force Canadian locale to avoid Chinese content.
            # Browser fingerprint + Chrome args + SOCKS5 proxy all work together
            # to signal "this browser is in Canada" to every website it visits.
            # The SOCKS5 proxy on moiria-coolify (Hetzner Germany) routes all
            # browser traffic through a European IP, bypassing Singapore/China.
            options = BrowserOption(
                viewport=BrowserViewport(width=1920, height=1080),
                screen=BrowserScreen(width=1920, height=1080),
                use_stealth=True,
                fingerprint=BrowserFingerprint(
                    devices=["desktop"],
                    operating_systems=["linux"],
                    locales=["fr-CA", "en-CA", "fr", "en"],
                ),
                cmd_args=[
                    "--lang=fr-CA",
                    "--accept-lang=fr-CA,en-CA,fr,en",
                    "--timezone=America/Toronto",
                ],
                proxies=[
                    BrowserProxy(
                        proxy_type="custom",
                        server="socks5://116.203.234.253:1080",
                    )
                ],
            )
            success = await asyncio.to_thread(self._session.browser.initialize, options)
            if success is False:
                raise RuntimeError("SDK failed to initialize browser (returned False).")
            self._browser_initialized = True

    async def browser_navigate(self, url: str, wait_for: str = "", screenshot: bool = False) -> dict:
        """Navigate via SDK operator so it tracks the active page for screenshots.

        IMPORTANT: We MUST navigate via the operator (not raw CDP) because the
        operator manages its own internal page list. When browser_screenshot()
        calls operator.screenshot(), it screenshots the page the operator knows
        about. If we navigate via CDP instead, the operator's page stays blank
        and screenshots are always white.
        """
        try:
            # Navigate via the operator so it tracks this as the active page
            result = await asyncio.to_thread(
                self._session.browser.operator.navigate, url
            )
            if not result or not result.get("success"):
                raise RuntimeError(f"Operator navigate failed: {result}")

            # Wait for additional selector if specified
            if wait_for:
                page = await self.get_cdp_page()
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    pass  # Non-critical — page may still have loaded

            nav_result = {
                "url": result.get("url", url),
                "success": True,
                "title": result.get("title", ""),
            }

            # If screenshot requested, use operator to capture the active page
            if screenshot:
                await asyncio.sleep(1)
                ss = await asyncio.to_thread(
                    self._session.browser.operator.screenshot, full_page=False
                )
                if ss:
                    nav_result["screenshot"] = ss

            return nav_result
        except Exception as e:
            raise RuntimeError(f"Navigation to '{url}' failed: {str(e)[:200]}")

    async def browser_screenshot(self) -> dict:
        """Screenshot — tries operator (SDK native) first, then CDP as fallback.

        The SDK's browser operator runs in the same context as the browser
        rendering, so it captures the actual visible content. CDP connects
        to a separate Playwright context that may not see the same pages,
        which is why CDP screenshots have been returning blank images.
        """
        # Strategy 1: SDK operator.screenshot — runs in the browser's own context
        try:
            if self._session and self._session.browser.is_initialized():
                logger.info("[AgentBay] Trying operator.screenshot (SDK native)")
                screenshot_data = await asyncio.to_thread(
                    self._session.browser.operator.screenshot, full_page=False
                )
                if screenshot_data and len(screenshot_data) > 500:
                    return {
                        "success": True,
                        "screenshot": screenshot_data,
                        "method": "operator",
                    }
                logger.info(
                    f"[AgentBay] Operator screenshot too small ({len(screenshot_data) if screenshot_data else 0} bytes)"
                )
        except Exception as e:
            logger.debug(f"[AgentBay] Operator screenshot failed: {e}")

        # Strategy 2: CDP — scan ALL contexts for a non-blank page
        try:
            if not self._cdp_browser or not self._cdp_browser.is_connected():
                await self._ensure_cdp_connection()

            # Log all contexts and pages for debugging
            ctx_count = len(self._cdp_browser.contexts)
            logger.info(
                f"[AgentBay] CDP screenshot: {ctx_count} context(s) available"
            )
            for i, ctx in enumerate(self._cdp_browser.contexts):
                page_count = len(ctx.pages)
                urls = []
                for pg in ctx.pages:
                    try:
                        urls.append(pg.url or "(none)")
                    except Exception:
                        urls.append("(error)")
                logger.info(
                    f"[AgentBay]   Context {i}: {page_count} page(s) — {', '.join(urls)}"
                )

            for ctx in self._cdp_browser.contexts:
                for pg in ctx.pages:
                    try:
                        url = pg.url
                        if url and url != "about:blank":
                            logger.info(
                                f"[AgentBay] CDP screenshot: using page {url[:100]}"
                            )
                            await asyncio.sleep(1)
                            img_bytes = await pg.screenshot(full_page=False)
                            if img_bytes and len(img_bytes) > 500:
                                return {
                                    "success": True,
                                    "screenshot": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}",
                                    "method": "cdp-existing-page",
                                }
                            logger.info(
                                f"[AgentBay] CDP screenshot too small: {len(img_bytes) if img_bytes else 0} bytes"
                            )
                    except Exception as e:
                        logger.debug(f"[AgentBay] CDP page screenshot failed: {e}")
                        continue
        except Exception as e:
            logger.debug(f"[AgentBay] CDP screenshot strategy failed: {e}")

        return {"success": False, "error": "All screenshot strategies failed"}


    async def browser_click(self, selector: str) -> dict:
        """Click via Playwright CDP (~0.1s)."""
        page = await self.get_cdp_page()

        try:
            await page.click(selector, timeout=10000)
            return {"success": True, "selector": selector}
        except Exception:
            # Fallback to operator
            from agentbay import ActOptions
            await asyncio.to_thread(
                self._session.browser.operator.act,
                ActOptions(action=f"click on {selector}")
            )
            return {"success": True, "selector": selector, "fallback": "operator"}

    async def browser_type(self, selector: str, text: str) -> dict:
        """Type via Playwright CDP (~0.1s)."""
        page = await self.get_cdp_page()

        try:
            await page.fill(selector, text, timeout=10000)
            return {"success": True, "selector": selector, "text": text}
        except Exception:
            # Fallback to operator
            from agentbay import ActOptions
            action_msg = f"Click on '{selector}' and type '{text}'"
            await asyncio.to_thread(self._session.browser.operator.act, ActOptions(action=action_msg))
            return {"success": True, "selector": selector, "text": text, "fallback": "operator"}
        return {"success": True, "selector": selector, "text": text}

    async def browser_login(self, url: str, login_config: str) -> dict:
        """Perform an automated login using AgentBay's built-in login skill.

        This leverages AgentBay's AI-driven login capability to handle complex
        login flows including CAPTCHAs, OTP inputs, and multi-step authentication.

        Args:
            url: The login page URL to navigate to first.
            login_config: JSON string with login configuration, e.g.
                          '{"api_key": "xxx", "skill_id": "yyy"}'
        """
        if not self._session or self._image_type != "browser":
            await self.create_session("browser_latest")
        await self._ensure_browser_initialized()

        # Navigate to the login page first
        await asyncio.to_thread(self._session.browser.operator.navigate, url)

        # Execute the login skill
        result = await asyncio.to_thread(
            self._session.browser.operator.login,
            login_config,
            use_vision=True,
        )
        return {
            "success": result.success,
            "message": result.message or "",
        }

    # ─── Code Operations ──────────────────────────

    async def code_execute(self, language: str, code: str, timeout: int = 30) -> dict:
        """Execute code in code space using SDK."""
        lang_map = {
            "python": "python",
            "bash": "bash",
            "shell": "bash",
            "node": "node",
            "javascript": "node",
        }
        sdk_lang = lang_map.get(language.lower(), "python")

        if not self._session or self._image_type not in ("code", "code_latest"):
            await self.create_session("code_latest")

        result = await asyncio.to_thread(self._session.code.run_code, code, sdk_lang)

        return {
            "stdout": result.result if result.success else "",
            "stderr": result.error_message if not result.success else "",
            "exit_code": 0 if result.success else 1,
            "success": result.success,
        }

    # ─── Browser: Extract & Observe ───────────────────

    async def browser_extract(self, instruction: str, selector: str = "") -> dict:
        """Extract structured data from current page using natural language instruction."""
        await self._ensure_browser_initialized()
        
        # Wait for dynamic content and SPA rendering before extracting
        await asyncio.sleep(3)

        from agentbay._common.models.browser_operator import ExtractOptions
        # Use a generic dict schema since we cannot define a Pydantic model at runtime
        options = ExtractOptions(
            instruction=instruction,
            schema=dict,
            selector=selector or None,
        )
        success, data = await asyncio.to_thread(
            self._session.browser.operator.extract, options
        )
        return {"success": success, "data": data}

    async def browser_observe(self, instruction: str, selector: str = "") -> dict:
        """Observe the current page state and return interactive elements."""
        await self._ensure_browser_initialized()
        
        # Wait for dynamic content and SPA rendering before observing
        await asyncio.sleep(3)

        from agentbay._common.models.browser_operator import ObserveOptions
        options = ObserveOptions(
            instruction=instruction,
            selector=selector or None,
        )
        success, results = await asyncio.to_thread(
            self._session.browser.operator.observe, options
        )
        # Convert ObserveResult objects to dicts for serialization
        result_dicts = []
        for r in (results or []):
            result_dicts.append(vars(r) if hasattr(r, "__dict__") else str(r))
        return {"success": success, "elements": result_dicts}

    # ─── Command (Shell) Operations ──────────────────

    async def command_exec(self, command: str, timeout_ms: int = 50000, cwd: str = "") -> dict:
        """Execute a shell command in the AgentBay environment."""
        if not self._session:
            await self.create_session("linux_latest")

        result = await asyncio.to_thread(
            self._session.command.exec,
            command,
            timeout_ms=timeout_ms,
            cwd=cwd or None,
        )
        return {
            "success": result.success,
            "stdout": getattr(result, "stdout", "") or getattr(result, "output", "") or "",
            "stderr": getattr(result, "stderr", "") or "",
            "exit_code": getattr(result, "exit_code", -1),
            "error_message": result.error_message or "",
        }

    # ─── Computer Operations ──────────────────────────

    async def _ensure_computer_session(self):
        """Ensure a computer (linux or windows desktop) session is active."""
        if not self._session or self._image_type not in ("computer", "linux_latest", "windows_latest"):
            await self.create_session("linux_latest")

    async def computer_screenshot(self) -> dict:
        """Take a screenshot of the desktop.

        Tries the standard screenshot() API first, then falls back to
        beta_take_screenshot() for cloud environments that don't support
        the standard API yet.
        """
        await self._ensure_computer_session()
        
        # Wait briefly for UI animations/rendering to settle
        await asyncio.sleep(2)

        try:
            result = await asyncio.to_thread(self._session.computer.screenshot)
            # Some cloud environments return success=False with a message
            # telling us to use beta_take_screenshot() instead of throwing.
            if not result.success and "beta_take_screenshot" in (result.error_message or ""):
                logger.info("[AgentBay] screenshot() unsupported, falling back to beta_take_screenshot()")
                result = await asyncio.to_thread(self._session.computer.beta_take_screenshot)
        except Exception as e:
            # Also handle the case where it raises an exception
            if "beta_take_screenshot" in str(e):
                logger.info("[AgentBay] Falling back to beta_take_screenshot() after exception")
                result = await asyncio.to_thread(self._session.computer.beta_take_screenshot)
            else:
                raise
        return {
            "success": result.success,
            "data": getattr(result, "data", None),
            "error_message": result.error_message or "",
        }

    async def computer_click(self, x: int, y: int, button: str = "left") -> dict:
        """Click the mouse at coordinates (x, y)."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.click_mouse, x, y, button)
        return {"success": result.success, "x": x, "y": y, "button": button}

    async def computer_input_text(self, text: str) -> dict:
        """Input text at the current cursor position."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.input_text, text)
        return {"success": result.success, "text": text}

    async def computer_press_keys(self, keys: list, hold: bool = False) -> dict:
        """Press keyboard keys (e.g. ['ctrl', 'c'] for Ctrl+C)."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.press_keys, keys, hold=hold)
        return {"success": result.success, "keys": keys, "hold": hold}

    async def computer_scroll(self, x: int, y: int, direction: str = "down", amount: int = 1) -> dict:
        """Scroll the screen at position (x, y)."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(
            self._session.computer.scroll, x, y, direction=direction, amount=amount
        )
        return {"success": result.success, "direction": direction, "amount": amount}

    async def computer_move_mouse(self, x: int, y: int) -> dict:
        """Move mouse to coordinates (x, y) without clicking."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.move_mouse, x, y)
        return {"success": result.success, "x": x, "y": y}

    async def computer_drag_mouse(
        self, from_x: int, from_y: int, to_x: int, to_y: int, button: str = "left"
    ) -> dict:
        """Drag mouse from (from_x, from_y) to (to_x, to_y)."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(
            self._session.computer.drag_mouse, from_x, from_y, to_x, to_y, button=button
        )
        return {"success": result.success, "from": [from_x, from_y], "to": [to_x, to_y]}

    async def computer_get_screen_size(self) -> dict:
        """Get the screen resolution."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.get_screen_size)
        return {
            "success": result.success,
            "data": getattr(result, "data", None),
            "error_message": result.error_message or "",
        }

    async def computer_start_app(self, cmd: str, work_dir: str = "") -> dict:
        """Start an application by its command."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(
            self._session.computer.start_app, cmd, work_directory=work_dir
        )
        return {
            "success": result.success,
            "data": getattr(result, "data", None),
            "error_message": result.error_message or "",
        }

    async def computer_get_cursor_position(self) -> dict:
        """Get current cursor position."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.get_cursor_position)
        return {
            "success": result.success,
            "data": getattr(result, "data", None),
            "error_message": result.error_message or "",
        }

    async def computer_get_active_window(self) -> dict:
        """Get info about the currently active window."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.get_active_window)
        window = getattr(result, "window", None)
        return {
            "success": result.success,
            "window": vars(window) if window and hasattr(window, "__dict__") else str(window),
            "error_message": result.error_message or "",
        }

    async def computer_activate_window(self, window_id: int) -> dict:
        """Activate (bring to front) a window by its ID."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.activate_window, window_id)
        return {"success": result.success, "window_id": window_id}

    async def computer_list_visible_apps(self) -> dict:
        """List currently visible/running applications."""
        await self._ensure_computer_session()
        result = await asyncio.to_thread(self._session.computer.list_visible_apps)
        data = getattr(result, "data", [])
        # Convert process objects to dicts
        apps = []
        for p in (data or []):
            apps.append(vars(p) if hasattr(p, "__dict__") else str(p))
        return {
            "success": result.success,
            "apps": apps,
            "error_message": result.error_message or "",
        }

    # ─── Live Preview Support ──────────────────────────

    async def get_live_url(self) -> str | None:
        """Get the VNC/viewer URL for the current computer session.

        Calls session.get_link() which returns a shareable viewer URL
        for the cloud desktop. Returns None if no session is active
        or the API call fails.
        """
        if not self._session:
            return None
        try:
            result = await asyncio.to_thread(self._session.get_link)
            if result.success and result.data:
                logger.info(f"[AgentBay] Got live URL: {str(result.data)[:80]}...")
                return result.data
            logger.warning(f"[AgentBay] get_link() failed: {result.error_message}")
            return None
        except Exception as e:
            logger.warning(f"[AgentBay] Failed to get live URL: {e}")
            return None

    async def get_desktop_snapshot_base64(self) -> str | None:
        """Take a quick desktop screenshot and return compressed base64 JPEG.

        Used for live preview panel. Calls the same screenshot API as
        computer_screenshot() but without the sleep delay, and compresses
        the result for efficient WebSocket transfer.
        Returns data:image/jpeg;base64,... or None on failure.
        """
        if not self._session:
            return None
        try:
            # Use the same screenshot logic as computer_screenshot()
            try:
                result = await asyncio.to_thread(self._session.computer.screenshot)
                if not result.success and "beta_take_screenshot" in (result.error_message or ""):
                    result = await asyncio.to_thread(self._session.computer.beta_take_screenshot)
            except Exception as e:
                if "beta_take_screenshot" in str(e):
                    result = await asyncio.to_thread(self._session.computer.beta_take_screenshot)
                else:
                    raise

            screenshot_data = getattr(result, "data", None)
            if not screenshot_data:
                return None

            # Compress to JPEG base64 for live preview
            import base64
            from io import BytesIO
            from PIL import Image

            img = Image.open(BytesIO(screenshot_data))
            # Resize to max 1920px wide for live preview (up from 1280px to preserve details)
            if img.width > 1920:
                ratio = 1920 / img.width
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=80, optimize=True)
            b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        except Exception as e:
            logger.warning(f"[AgentBay] Desktop snapshot failed: {e}")
            return None

    async def get_browser_snapshot_base64(self) -> str | None:
        """Take a quick browser screenshot and return compressed base64 JPEG.

        Used for live preview panel — no wait/sleep since we want
        the snapshot to reflect the current state immediately.
        Returns data:image/jpeg;base64,... or None on failure.
        """
        if not self._session:
            logger.info("[AgentBay] Browser snapshot skipped: No active session")
            return None
        if not getattr(self, "_browser_initialized", False):
            logger.info("[AgentBay] Browser snapshot skipped: Browser not initialized")
            return None
        
        try:
            screenshot_data = await asyncio.to_thread(
                self._session.browser.operator.screenshot, full_page=False
            )
            if not screenshot_data:
                logger.info("[AgentBay] Browser snapshot returned empty data")
                return None

            # Compress screenshot to JPEG base64 for efficient transfer
            import base64
            from io import BytesIO
            from PIL import Image

            if isinstance(screenshot_data, str):
                # The AgentBay SDK may return a raw base64 string without proper
                # padding. Normalize by stripping whitespace and adding padding chars.
                screenshot_data = screenshot_data.strip()
                # Remove data URI prefix if present (e.g., "data:image/png;base64,")
                if "," in screenshot_data:
                    screenshot_data = screenshot_data.split(",", 1)[1]
                # Add base64 padding if missing
                missing_padding = len(screenshot_data) % 4
                if missing_padding:
                    screenshot_data += "=" * (4 - missing_padding)
                screenshot_data = base64.b64decode(screenshot_data)


            img = Image.open(BytesIO(screenshot_data))
            # Resize to max 1920px wide for live preview (up from 1280px to preserve details)
            if img.width > 1920:
                ratio = 1920 / img.width
                img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=80, optimize=True)
            b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
            return f"data:image/jpeg;base64,{b64}"
        except Exception as e:
            logger.warning(f"[AgentBay] Browser snapshot failed: {e}")
            return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()


# ─── Session Cache for Tool Executions ──────────────────────────
# Key: (agent_id, session_id, image_type) so each ChatSession gets
# its own independent AgentBay instance for browser/computer/code.
# Previously keyed by (agent_id, image_type) which meant all users
# of the same Agent shared one browser/desktop — causing conflicts.

_agentbay_sessions: dict[tuple[uuid.UUID, str, str], tuple[AgentBayClient, datetime]] = {}
_AGENTBAY_SESSION_TIMEOUT = timedelta(minutes=5)


AGENTBAY_API_URL = "https://api.agentbay.ai/v1"


async def get_agentbay_api_key_for_agent(agent_id: uuid.UUID, db=None) -> Optional[str]:
    """Return the configured AgentBay API key for the given agent.

    Resolution order:
    1. Per-agent ChannelConfig (channel_type='agentbay') — set via Agent detail page
    2. Global Tool.config.api_key (category='agentbay') — set via Company Settings
    """
    from app.models.channel_config import ChannelConfig
    from app.models.tool import Tool
    from sqlalchemy import select
    from app.database import async_session
    from app.core.security import decrypt_data
    from app.config import get_settings

    async def _fetch(session):
        # 1) Check per-agent ChannelConfig first (highest priority)
        result = await session.execute(
            select(ChannelConfig).where(
                ChannelConfig.agent_id == agent_id,
                ChannelConfig.channel_type == "agentbay",
                ChannelConfig.is_configured == True,
            )
        )
        config = result.scalar_one_or_none()
        if config and config.app_secret:
            # Try to decrypt, fallback to plaintext if it fails
            try:
                return decrypt_data(config.app_secret, get_settings().SECRET_KEY)
            except Exception:
                return config.app_secret

        # 2) Fallback: check global Tool.config.api_key for agentbay tools.
        #
        # Only agentbay_browser_navigate (the "primary" AgentBay tool) has a
        # config_schema with an api_key field, so it is the only tool whose
        # config is ever populated with a key via the Company Settings UI.
        # We therefore query it first, then fall back to scanning all agentbay
        # tools — this prevents a non-deterministic .limit(1) from returning a
        # tool with an empty config (e.g. agentbay_computer_screenshot), which
        # would silently return None even when a key IS configured.
        tool_result = await session.execute(
            select(Tool).where(
                Tool.name == "agentbay_browser_navigate",
                Tool.enabled == True,
            ).limit(1)
        )
        tool = tool_result.scalar_one_or_none()

        # Also scan all agentbay tools in case the key was stored differently
        if not (tool and tool.config and tool.config.get("api_key")):
            all_result = await session.execute(
                select(Tool).where(
                    Tool.category == "agentbay",
                    Tool.enabled == True,
                )
            )
            for candidate in all_result.scalars().all():
                if candidate.config and candidate.config.get("api_key"):
                    tool = candidate
                    break

        if tool and tool.config and tool.config.get("api_key"):
            api_key = tool.config["api_key"]
            # Try to decrypt (global config is encrypted via _encrypt_sensitive_fields)
            try:
                return decrypt_data(api_key, get_settings().SECRET_KEY)
            except Exception:
                return api_key

        return None

    if db:
        return await _fetch(db)
    async with async_session() as session:
        return await _fetch(session)


async def test_agentbay_channel(agent_id: uuid.UUID, current_user, db) -> dict:
    """Test AgentBay connectivity."""
    key = await get_agentbay_api_key_for_agent(agent_id, db)
    if not key:
        return {"ok": False, "error": "AgentBay not configured"}
    try:
        from agentbay import AgentBay, CreateSessionParams
        sdk = AgentBay(api_key=key)
        # Override SDK endpoint to use intl API (SDK defaults to cn-shanghai)
        sdk.client._endpoint = 'wuyingai.ap-southeast-1.aliyuncs.com'
        # Using linux_latest instead of browser_latest. AgentBay tokens may be
        # scoped/bound to specific instance types, and requesting browser_latest
        # might trigger an 'InvalidParameter.Authorization' error for this key.
        result = await asyncio.to_thread(sdk.create, CreateSessionParams(image_id="linux_latest"))
        if result.success:
            if result.session:
                await asyncio.to_thread(result.session.delete)
            return {"ok": True, "message": "✅ Successfully connected to AgentBay API"}
        return {"ok": False, "error": result.error_message}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def get_agentbay_client_for_agent(agent_id: uuid.UUID, image_type: str, session_id: str = "") -> AgentBayClient:
    """Get or create AgentBay client for agent.

    Sessions are cached per (agent_id, session_id, image_type) so that each
    ChatSession gets its own independent AgentBay instance. Multiple users
    chatting with the same Agent will each have isolated browser/desktop/code
    environments.

    Args:
        agent_id: The agent UUID.
        image_type: One of 'browser', 'computer', 'code'.
        session_id: The ChatSession ID. Defaults to '' for backward compat
                    (e.g. test_agentbay_channel, single-session callers).
    """

    now = datetime.now()
    cache_key = (agent_id, session_id, image_type)

    if cache_key in _agentbay_sessions:
        client, last_used = _agentbay_sessions[cache_key]
        if now - last_used < _AGENTBAY_SESSION_TIMEOUT:
            # Session still valid, refresh timestamp and reuse
            _agentbay_sessions[cache_key] = (client, now)
            return client
        else:
            # Session expired, close and remove
            logger.info(f"[AgentBay] Session expired for {image_type} (session={session_id[:8]}), closing")
            await client.close_session()
            del _agentbay_sessions[cache_key]

    from app.services.agent_tools import _get_tool_config

    tool_config = await _get_tool_config(agent_id, "agentbay_browser_navigate")
    api_key = None
    region = 'intl'  # Default to Singapore international endpoint

    if tool_config:
        # Get API key from tool config
        if tool_config.get("api_key"):
            api_key = tool_config.get("api_key")
            from app.core.security import decrypt_data
            from app.config import get_settings
            try:
                api_key = decrypt_data(api_key, get_settings().SECRET_KEY)
            except Exception:
                pass  # Fallback if it's somehow plaintext
        
        # Get region preference from tool config
        region = tool_config.get("region", "intl")
    else:
        api_key = await get_agentbay_api_key_for_agent(agent_id)

    if not api_key:
        raise RuntimeError("AgentBay not configured for this agent. Please configure in Tools > AgentBay.")

    logger.info(f"[AgentBay] Creating client for agent={agent_id}, region={region}")
    client = AgentBayClient(api_key, region=region)

    if image_type == "browser":
        await client.create_session("browser_latest")
        # Inject stored cookies after browser initialization
        await _inject_credentials(client, agent_id)
    elif image_type == "computer":
        # Read OS preference from tool config (default: windows)
        os_type = (tool_config or {}).get("os_type", "windows")
        computer_image = "windows_latest" if os_type == "windows" else "linux_latest"
        logger.info(f"[AgentBay] Creating computer session with OS: {os_type} (image: {computer_image}) for session={session_id[:8]}")
        await client.create_session(computer_image)
    else:
        await client.create_session("code_latest")

    _agentbay_sessions[cache_key] = (client, now)
    return client


async def cleanup_agentbay_sessions():
    """Clean up expired AgentBay sessions."""
    now = datetime.now()
    expired = [
        cache_key for cache_key, (client, last_used) in _agentbay_sessions.items()
        if now - last_used > _AGENTBAY_SESSION_TIMEOUT
    ]
    for cache_key in expired:
        client, _ = _agentbay_sessions.pop(cache_key)
        agent_id, session_id, image_type = cache_key
        logger.info(f"[AgentBay] Cleaning up expired {image_type} session for agent {agent_id} (session={session_id[:8]})")
        await client.close_session()


async def _inject_credentials(client: AgentBayClient, agent_id: uuid.UUID):
    """Inject stored cookies into the browser via CDP after initialization.

    Reads all 'active' credentials with cookies from the agent_credentials table,
    decrypts cookies_json, and injects them via a Playwright Node.js script that
    connects to Chrome's CDP port (localhost:9222).

    This runs automatically after every browser session creation. If no credentials
    exist or injection fails, it logs a warning but does not block the session.
    """
    import json
    from app.database import async_session as async_session_factory
    from app.models.agent_credential import AgentCredential
    from sqlalchemy import select
    from app.core.security import decrypt_data
    from app.config import get_settings

    settings = get_settings()

    # Fetch active credentials with stored cookies
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(AgentCredential).where(
                    AgentCredential.agent_id == agent_id,
                    AgentCredential.status == "active",
                    AgentCredential.cookies_json.isnot(None),
                )
            )
            credentials = result.scalars().all()
    except Exception as e:
        logger.warning(f"[AgentBay] Failed to query credentials for injection: {e}")
        return

    if not credentials:
        return  # No cookies to inject

    # Collect and decrypt all cookies
    all_cookies = []
    for cred in credentials:
        try:
            raw = decrypt_data(cred.cookies_json, settings.SECRET_KEY)
            cookies = json.loads(raw)
            if isinstance(cookies, list):
                all_cookies.extend(cookies)
        except Exception as e:
            logger.warning(f"[AgentBay] Failed to decrypt cookies for {cred.platform}: {e}")

    if not all_cookies:
        return

    # Ensure browser is initialized before injection (Chrome must be running)
    try:
        await client._ensure_browser_initialized()
    except Exception as e:
        logger.warning(f"[AgentBay] Cannot inject cookies — browser not initialized: {e}")
        return

    # Build Node.js injection script.
    # Use base64 encoding to write the script to the current working dir (not /tmp,
    # which may lack write permissions in the Wuying browser sandbox).
    #
    # Cookies stored in DB were already sanitized at export time (sameSite title-cased,
    # expires:-1 removed, domain without leading dot), so we only do a defensive
    # re-sanitize here in case older records were stored before the fix.
    import base64 as _base64
    cookies_json_str = json.dumps(all_cookies)
    inject_script = r"""
const { chromium } = require('/usr/local/lib/node_modules/playwright');
(async () => {
    try {
        const browser = await chromium.connectOverCDP('http://localhost:9222');
        const context = browser.contexts()[0];
        const rawCookies = """ + cookies_json_str + r""";

        // Defensive sanitize: normalize sameSite casing and strip invalid expires
        const sameSiteMap = { none: 'None', lax: 'Lax', strict: 'Strict' };
        const cookies = rawCookies.map(c => {
            const out = { ...c };
            if (out.sameSite != null) {
                out.sameSite = sameSiteMap[String(out.sameSite).toLowerCase()] || 'Lax';
            }
            if (out.expires != null && out.expires <= 0) {
                delete out.expires;
            }
            // Ensure domain has leading dot for subdomain matching
            if (out.domain && !out.domain.startsWith('.')) {
                out.domain = '.' + out.domain;
            }
            return out;
        });

        let injected = 0;
        let failed = 0;
        // Inject one at a time so a single bad cookie doesn't break the rest
        for (const cookie of cookies) {
            try {
                await context.addCookies([cookie]);
                injected++;
            } catch (e) {
                failed++;
                if (failed <= 3) {
                    // Log first few failures to aid debugging
                    console.error('INJECT_SKIP:' + e.message + ' cookie=' + JSON.stringify(cookie).slice(0, 200));
                }
            }
        }
        console.log('INJECT_OK:' + injected + ' injected, ' + failed + ' skipped');
        process.exit(0);
    } catch (e) {
        console.error('INJECT_FAIL:' + e.message);
        process.exit(1);
    }
})();
"""


    try:
        # Write script via base64 decode to avoid shell quoting issues and /tmp permission errors
        script_b64 = _base64.b64encode(inject_script.encode('utf-8')).decode('ascii')
        write_result = await asyncio.to_thread(
            client._session.command.exec,
            f"echo '{script_b64}' | /usr/bin/base64 -d > tc_inject_cookies.js",
        )
        write_ok = getattr(write_result, 'success', False)
        logger.info(f"[AgentBay] Cookie inject script write: success={write_ok}")

        # Execute the injection script
        exec_result = await asyncio.to_thread(
            client._session.command.exec,
            "node tc_inject_cookies.js",
            timeout_ms=15000,
        )
        stdout = getattr(exec_result, 'stdout', '') or getattr(exec_result, 'output', '') or ''
        stderr = getattr(exec_result, 'stderr', '') or ''

        if "INJECT_OK" in stdout:
            logger.info(f"[AgentBay] Cookie injection successful for agent {agent_id}: {stdout.strip()[:100]}")
            # Update last_injected_at for all injected credentials
            try:
                from datetime import timezone as tz
                now = datetime.now(tz.utc)
                async with async_session_factory() as db:
                    for cred in credentials:
                        cred.last_injected_at = now
                        db.add(cred)
                    await db.commit()
            except Exception as e:
                logger.warning(f"[AgentBay] Failed to update last_injected_at: {e}")
        else:
            logger.warning(f"[AgentBay] Cookie injection may have failed: stdout={stdout[:200]}, stderr={stderr[:200]}")
    except Exception as e:
        logger.warning(f"[AgentBay] Cookie injection error: {e}")