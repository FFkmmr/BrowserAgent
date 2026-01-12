"""
Контроллер браузера на основе Playwright
"""
from typing import Optional
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
    
    async def start(self):
        """Запуск браузера"""
        log.info("Запуск браузера...")
        
        self.playwright = await async_playwright().start()
        
        # Выбор типа браузера
        browser_type = getattr(self.playwright, config.BROWSER_TYPE)
        
        self.browser = await browser_type.launch(
            headless=config.HEADLESS,
            slow_mo=config.SLOW_MO,
        )
        
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
