"""Контроллер браузера на основе Playwright."""

import asyncio
from typing import Optional

import aiohttp
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from config.config import config
from src.utils.logger import log


class BrowserController:
    """Управление браузером через Playwright"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._connected_over_cdp: bool = False

    @staticmethod
    def _score_page_for_control(page: Page) -> int:
        url = (page.url or "").strip()
        if not url:
            return -50
        if url.startswith("chrome-extension://"):
            return -1000
        if url.startswith("chrome://") or url.startswith("devtools://"):
            return -900
        if url.startswith("about:"):
            return -100
        # Prefer Gmail if it's already open
        if url.startswith("https://mail.google.com"):
            return 100
        if url.startswith("https://") or url.startswith("http://"):
            return 50
        return 0

    async def _pick_control_page(self) -> Page:
        if not self.context:
            raise RuntimeError("Browser context is not initialized")

        pages = [p for p in (self.context.pages or []) if not p.is_closed()]
        if pages:
            best = max(pages, key=self._score_page_for_control)
            if self._score_page_for_control(best) > 0:
                log.info(f"CDP: выбрана вкладка для управления: {best.url}")
                return best

        # Fallback: open a fresh tab (real page, not sidepanel)
        page = await self.context.new_page()
        log.info("CDP: открыта новая вкладка для управления")
        return page

    async def _probe_cdp(self) -> None:
        """Проверяет доступность CDP endpoint до попытки connect_over_cdp.

        Без этого Playwright может долго ждать соединения, что выглядит как "завис".
        """

        base = (config.CHROME_CDP_URL or "").rstrip("/")
        probe_url = f"{base}/json/version"
        timeout_s = max(int(getattr(config, "CDP_CONNECT_TIMEOUT_SECONDS", 5) or 5), 1)

        try:
            timeout = aiohttp.ClientTimeout(total=timeout_s)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(probe_url) as resp:
                    # /json/version обычно возвращает JSON с Browser/WebSocketDebuggerUrl
                    if resp.status != 200:
                        raise RuntimeError(f"HTTP {resp.status}")
                    await resp.read()
        except Exception as e:
            raise RuntimeError(
                "Chrome CDP endpoint недоступен. "
                f"Проверьте, что Chrome запущен с --remote-debugging-port=9222 и доступен {probe_url}. "
                "Либо уберите CHROME_CDP_URL из .env, чтобы агент запускал отдельный браузер Playwright. "
                f"(timeout={timeout_s}s, error={e})"
            )
    
    async def start(self):
        """Запуск браузера"""
        log.info("Запуск браузера...")
        
        self.playwright = await async_playwright().start()

        # Если задан CDP URL — подключаемся к уже запущенному Chrome/Chromium.
        # Это позволяет работать в том же браузере, где открыт extension.
        if config.CHROME_CDP_URL:
            log.info(f"Подключение к Chrome по CDP: {config.CHROME_CDP_URL}")

            await self._probe_cdp()

            timeout_s = max(int(getattr(config, "CDP_CONNECT_TIMEOUT_SECONDS", 5) or 5), 1)
            self.browser = await asyncio.wait_for(
                self.playwright.chromium.connect_over_cdp(config.CHROME_CDP_URL),
                timeout=timeout_s,
            )
            self._connected_over_cdp = True

            # Берём первый доступный контекст/таб или создаём новый таб
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                # На CDP это бывает редко, но оставим fallback
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

            self.page = await self._pick_control_page()

            log.success("Подключение к Chrome по CDP успешно")
            return self.page
        
        # Выбор типа браузера
        browser_type = getattr(self.playwright, config.BROWSER_TYPE)

        launch_kwargs = {
            "headless": config.HEADLESS,
            "slow_mo": config.SLOW_MO,
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL

        self.browser = await browser_type.launch(**launch_kwargs)
        
        # Создание контекста с viewport
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Создание страницы
        self.page = await self.context.new_page()
        
        log.success(f"Браузер {config.BROWSER_TYPE} запущен успешно")
        
        return self.page
    
    async def close(self):
        """Закрытие браузера"""
        log.info("Закрытие браузера...")

        # При CDP-подключении обычно не хотим закрывать реальный Chrome пользователя.
        if self._connected_over_cdp and config.KEEP_BROWSER_OPEN:
            if self.playwright:
                await self.playwright.stop()
            log.info("CDP-сессия закрыта (Chrome оставлен открытым)")
            return
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        log.info("Браузер закрыт")
    
    async def get_page(self) -> Page:
        """Получить текущую страницу"""
        if not self.page:
            await self.start()
        return self.page
    
    async def new_page(self) -> Page:
        """Создать новую страницу"""
        if not self.context:
            await self.start()
        
        self.page = await self.context.new_page()
        return self.page
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
