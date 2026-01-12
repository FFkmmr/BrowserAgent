"""
Анализатор веб-страниц
"""
from typing import Dict, Any
from playwright.async_api import Page
from src.utils.logger import log
from src.utils.dom_utils import simplify_dom, extract_interactive_elements
from src.utils.types import PageState


class PageAnalyzer:
    """Анализ и понимание веб-страниц"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def analyze(self) -> PageState:
        """
        Полный анализ текущей страницы
        Возвращает упрощенное представление для LLM
        """
        log.info(f"Анализ страницы: {self.page.url}")
        
        # Получаем базовую информацию
        url = self.page.url
        title = await self.page.title()
        
        # Получаем HTML
        html_content = await self.page.content()
        
        # Упрощаем DOM
        simplified = simplify_dom(html_content)
        
        # Извлекаем интерактивные элементы
        elements = extract_interactive_elements(html_content)
        
        log.debug(f"Найдено {len(elements)} интерактивных элементов")
        
        return PageState(
            url=url,
            title=title,
            simplified_dom=simplified[:10000],  # Ограничиваем размер
            interactive_elements=elements[:50],  # Берём первые 50 элементов
        )
    
    async def get_element_info(self, selector: str) -> Dict[str, Any]:
        """Получить информацию об элементе"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            
            if not element:
                return {"found": False}
            
            return {
                "found": True,
                "text": await element.text_content(),
                "visible": await element.is_visible(),
                "enabled": await element.is_enabled(),
            }
        except Exception as e:
            log.warning(f"Элемент {selector} не найден: {e}")
            return {"found": False, "error": str(e)}
    
    async def extract_text(self, selector: str = "body") -> str:
        """Извлечь текст со страницы"""
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                text = await element.text_content()
                return text.strip() if text else ""
        except Exception as e:
            log.error(f"Ошибка извлечения текста: {e}")
        
        return ""
    
    async def take_screenshot(self, path: str = "screenshot.png") -> str:
        """Сделать скриншот страницы"""
        try:
            await self.page.screenshot(path=path, full_page=False)
            log.info(f"Скриншот сохранён: {path}")
            return path
        except Exception as e:
            log.error(f"Ошибка создания скриншота: {e}")
            return ""
