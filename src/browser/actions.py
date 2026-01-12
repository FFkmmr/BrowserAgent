"""
Библиотека действий в браузере
"""
from typing import Any, Dict
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout
from src.utils.logger import log
from src.utils.types import ActionResult, ActionType
import asyncio
import inspect


class BrowserActions:
    """Все возможные действия агента в браузере"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def execute(self, action_type: ActionType, parameters: Dict[str, Any]) -> ActionResult:
        """
        Выполнить действие
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Маппинг действий на методы
            action_map = {
                ActionType.NAVIGATE: self.navigate,
                ActionType.CLICK: self.click,
                ActionType.TYPE: self.type_text,
                ActionType.SELECT: self.select_option,
                ActionType.SCROLL: self.scroll,
                ActionType.EXTRACT_TEXT: self.extract_text,
                ActionType.WAIT: self.wait,
                ActionType.GO_BACK: self.go_back,
                ActionType.GO_FORWARD: self.go_forward,
                ActionType.RELOAD: self.reload,
            }
            
            action_func = action_map.get(action_type)
            if not action_func:
                return ActionResult(
                    success=False,
                    error=f"Неизвестное действие: {action_type}"
                )
            
            # Выполняем действие (фильтруем лишние параметры, чтобы агент не падал)
            safe_parameters = parameters or {}
            try:
                sig = inspect.signature(action_func)
                allowed = set(sig.parameters.keys())
                filtered = {k: v for k, v in safe_parameters.items() if k in allowed}
                dropped = set(safe_parameters.keys()) - set(filtered.keys())
                if dropped:
                    log.debug(f"Игнорирую лишние параметры для {action_type.value}: {sorted(dropped)}")
                safe_parameters = filtered
            except Exception:
                pass

            result_data = await action_func(**safe_parameters)

            duration = asyncio.get_event_loop().time() - start_time

            # Normalize "soft" failures into ActionResult.success=False
            # (e.g., click() may return {clicked: False, error: "..."} instead of raising)
            success = True
            error = None
            if isinstance(result_data, dict):
                failure_flags = ("clicked", "typed", "selected")
                for flag in failure_flags:
                    if flag in result_data and result_data.get(flag) is False:
                        success = False
                        error = str(result_data.get("error") or f"{flag} failed")
                        break

            return ActionResult(
                success=success,
                data=result_data,
                error=error,
                duration=duration,
            )
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            log.error(f"Ошибка выполнения действия {action_type}: {e}")
            
            return ActionResult(
                success=False,
                error=str(e),
                duration=duration
            )
    
    # ==================== NAVIGATION ====================
    
    async def navigate(self, url: str) -> str:
        """Перейти по URL"""
        log.info(f"Переход на {url}")
        await self.page.goto(url, wait_until="domcontentloaded")
        return self.page.url
    
    async def go_back(self) -> str:
        """Назад"""
        log.info("Переход назад")
        await self.page.go_back()
        return self.page.url
    
    async def go_forward(self) -> str:
        """Вперёд"""
        log.info("Переход вперёд")
        await self.page.go_forward()
        return self.page.url
    
    async def reload(self) -> str:
        """Перезагрузка страницы"""
        log.info("Перезагрузка страницы")
        await self.page.reload()
        return self.page.url
    
    # ==================== INTERACTION ====================
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Клик по элементу"""
        log.info(f"Клик по элементу: {selector}")
        
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.click(selector)
            return {"clicked": True, "selector": selector}
        except PlaywrightTimeout:
            log.warning(f"Элемент не найден: {selector}")
            return {"clicked": False, "error": "Element not found"}
    
    async def type_text(self, selector: str, text: str, clear: bool = True) -> Dict[str, Any]:
        """Ввод текста"""
        log.info(f"Ввод текста в {selector}: {text[:50]}...")
        
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            
            if clear:
                await self.page.fill(selector, text)
            else:
                await self.page.type(selector, text)
            
            return {"typed": True, "selector": selector, "text": text}
        except PlaywrightTimeout:
            return {"typed": False, "error": "Element not found"}
    
    async def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        """Выбор опции в select"""
        log.info(f"Выбор опции {value} в {selector}")
        
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.select_option(selector, value)
            return {"selected": True, "selector": selector, "value": value}
        except PlaywrightTimeout:
            return {"selected": False, "error": "Element not found"}
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        """Прокрутка страницы"""
        log.info(f"Прокрутка {direction} на {amount}px")
        
        if direction == "down":
            await self.page.evaluate(f"window.scrollBy(0, {amount})")
        elif direction == "up":
            await self.page.evaluate(f"window.scrollBy(0, -{amount})")
        elif direction == "top":
            await self.page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        return {"scrolled": True, "direction": direction}
    
    # ==================== EXTRACTION ====================
    
    async def extract_text(self, selector: str = "body", limit: int = None) -> str:
        """Извлечь текст"""
        log.info(f"Извлечение текста из {selector}")
        
        try:
            if limit and limit > 0:
                # Берём первые N совпадений селектора
                await self.page.wait_for_selector(selector, timeout=10000)
                elements = await self.page.query_selector_all(selector)
                parts = []
                for el in elements[:limit]:
                    t = await el.text_content()
                    if t:
                        parts.append(t.strip())
                return "\n".join([p for p in parts if p])

            element = await self.page.wait_for_selector(selector, timeout=10000)
            text = await element.text_content()
            return text.strip() if text else ""
        except PlaywrightTimeout:
            return ""
    
    # ==================== WAITING ====================
    
    async def wait(self, milliseconds: int = 1000) -> Dict[str, Any]:
        """Ожидание"""
        log.info(f"Ожидание {milliseconds}ms")
        await asyncio.sleep(milliseconds / 1000)
        return {"waited": True, "duration": milliseconds}
