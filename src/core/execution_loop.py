"""
Execution Loop - основной цикл выполнения агента (ReAct Pattern)
"""
import asyncio
from typing import Optional
from src.utils.logger import log
from src.utils.types import ActionType, Action, ActionResult, AgentStep, TaskStatus
from src.ai.llm_client import ClaudeClient
from src.browser.browser_controller import BrowserController
from src.browser.page_analyzer import PageAnalyzer
from src.browser.actions import BrowserActions
from src.context.memory import ContextManager
from config.config import config


class ExecutionLoop:
    """
    Основной цикл выполнения агента
    Реализует ReAct паттерн: Observe → Reason → Act → Repeat
    """
    
    def __init__(self):
        self.llm_client = ClaudeClient()
        self.context_manager = ContextManager()
        self.browser: Optional[BrowserController] = None
        self.status = TaskStatus.IDLE
        self.current_step = 0
    
    async def execute_task(self, task_description: str) -> dict:
        """
        Главный метод - выполнение задачи от начала до конца
        """
        log.info(f"=== НАЧАЛО ВЫПОЛНЕНИЯ ЗАДАЧИ ===")
        log.info(f"Задача: {task_description}")
        
        # Инициализация
        self.context_manager.initialize_task(task_description)
        self.status = TaskStatus.EXECUTING
        self.current_step = 0
        
        # Запуск браузера
        self.browser = BrowserController()
        await self.browser.start()
        
        page = await self.browser.get_page()
        page_analyzer = PageAnalyzer(page)
        actions_executor = BrowserActions(page)
        
        task_completed = False
        final_result = None
        
        try:
            # Основной цикл
            while self.current_step < config.MAX_STEPS and not task_completed:
                self.current_step += 1
                log.info(f"\n--- ШАГ {self.current_step} ---")
                
                # 1. PERCEPTION - Анализ текущей страницы
                log.info("📊 Анализ страницы...")
                page_state = await page_analyzer.analyze()
                self.context_manager.update_page_state(page_state.__dict__)
                
                # 2. REASONING - Запрос к LLM для принятия решения
                log.info("🧠 Запрос к Claude...")
                messages = self.context_manager.build_messages_for_llm()
                
                response = await self.llm_client.get_next_action(messages)
                
                # Логируем reasoning
                if response['thinking']:
                    log.info(f"💭 Reasoning: {response['thinking'][:200]}...")
                
                # 3. ACTION - Выполнение действия
                if not response['tool_calls']:
                    log.warning("LLM не вернул tool call. Завершение.")
                    break
                
                tool_call = response['tool_calls'][0]  # Берём первый tool call
                tool_name = tool_call['name']
                tool_input = tool_call['input']
                
                log.info(f"🎯 Действие: {tool_name}({tool_input})")
                
                # Проверка на завершение задачи
                if tool_name == "task_complete":
                    task_completed = True
                    final_result = tool_input.get('result', 'Задача выполнена')
                    log.success(f"✅ Задача завершена: {final_result}")
                    break
                
                # Выполнение действия
                try:
                    action_type = ActionType(tool_name)
                except ValueError:
                    log.error(f"Неизвестное действие: {tool_name}")
                    continue
                
                action = Action(
                    type=action_type,
                    parameters=tool_input,
                    reasoning=response['thinking']
                )
                
                result = await actions_executor.execute(action_type, tool_input)
                
                # Логируем результат
                if result.success:
                    log.success(f"✓ Успешно за {result.duration:.2f}s")
                else:
                    log.error(f"✗ Ошибка: {result.error}")
                
                # 4. REFLECTION - Сохранение шага в память
                step = AgentStep(
                    step_number=self.current_step,
                    observation=f"URL: {page_state.url}, Title: {page_state.title}",
                    thought=response['thinking'],
                    action=action,
                    result=result
                )
                
                self.context_manager.add_step(step)
                
                # Небольшая пауза между шагами
                await asyncio.sleep(0.5)
            
            # Проверка завершения
            if not task_completed:
                if self.current_step >= config.MAX_STEPS:
                    log.warning(f"Достигнут лимит шагов: {config.MAX_STEPS}")
                    self.status = TaskStatus.FAILED
                    return {
                        'success': False,
                        'result': 'Превышен лимит шагов',
                        'steps': self.current_step
                    }
            
            self.status = TaskStatus.COMPLETED
            return {
                'success': True,
                'result': final_result or 'Задача выполнена',
                'steps': self.current_step
            }
            
        except Exception as e:
            log.error(f"Критическая ошибка: {e}", exc_info=True)
            self.status = TaskStatus.FAILED
            return {
                'success': False,
                'result': f'Ошибка: {str(e)}',
                'steps': self.current_step
            }
        
        finally:
            # Закрытие браузера
            log.info("Закрытие браузера...")
            await self.browser.close()
            log.info("=== ЗАДАЧА ЗАВЕРШЕНА ===\n")
    
    async def pause(self):
        """Приостановить выполнение"""
        self.status = TaskStatus.PAUSED
        log.info("Выполнение приостановлено")
    
    async def resume(self):
        """Возобновить выполнение"""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.EXECUTING
            log.info("Выполнение возобновлено")
