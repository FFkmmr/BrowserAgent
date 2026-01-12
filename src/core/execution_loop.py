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
        # Optional async callback(event_dict) for streaming updates (e.g., to extension)
        self.event_callback = None

    async def _emit(self, event: dict):
        if not self.event_callback:
            return
        try:
            await self.event_callback(event)
        except Exception:
            # Never break task execution due to telemetry
            pass
    
    async def execute_task(self, task_description: str) -> dict:
        """
        Главный метод - выполнение задачи от начала до конца
        """
        log.info(f"=== НАЧАЛО ВЫПОЛНЕНИЯ ЗАДАЧИ ===")
        log.info(f"Задача: {task_description}")
        await self._emit({"type": "agent_message", "role": "system", "text": "=== НАЧАЛО ВЫПОЛНЕНИЯ ЗАДАЧИ ==="})
        
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
        last_llm_message: str = ""
        last_extracted_text: str = ""
        
        try:
            # Основной цикл
            while self.current_step < config.MAX_STEPS and not task_completed:
                self.current_step += 1
                log.info(f"\n--- ШАГ {self.current_step} ---")
                await self._emit({"type": "agent_message", "role": "system", "text": f"--- ШАГ {self.current_step} ---"})
                
                # 1. PERCEPTION - Анализ текущей страницы
                log.info("📊 Анализ страницы...")
                page_state = await page_analyzer.analyze()
                self.context_manager.update_page_state(page_state.__dict__)
                await self._emit({"type": "agent_message", "role": "system", "text": f"Страница: {page_state.url}"})
                
                # 2. REASONING - Запрос к LLM для принятия решения
                log.info("🧠 Запрос к AI...")
                messages = self.context_manager.build_messages_for_llm()
                
                response = await self.llm_client.get_next_action(messages)
                last_llm_message = response.get('message', '') or response.get('thinking', '') or ""
                
                # Логируем reasoning
                if response['thinking']:
                    log.info(f"💭 Reasoning: {response['thinking'][:200]}...")
                    await self._emit({"type": "agent_message", "role": "assistant", "text": response['thinking']})
                
                # 3. ACTION - Выполнение действия
                if not response['tool_calls']:
                    log.warning("LLM не вернул tool call. Завершение.")
                    self.status = TaskStatus.FAILED
                    return {
                        'success': False,
                        'result': f"LLM не вернул tool call. Ответ модели: {last_llm_message[:500]}",
                        'steps': self.current_step
                    }
                
                tool_call = response['tool_calls'][0]  # Берём первый tool call
                tool_name = tool_call['name']
                tool_input = tool_call['input']
                
                log.info(f"🎯 Действие: {tool_name}({tool_input})")
                await self._emit({"type": "agent_message", "role": "system", "text": f"Действие: {tool_name} {tool_input}"})
                
                # Проверка на завершение задачи
                if tool_name == "task_complete":
                    task_completed = True
                    # Некоторые модели могут вернуть task_complete без result.
                    # В этом случае используем последний успешно извлечённый текст (если есть).
                    final_result = tool_input.get('result') or (last_extracted_text.strip() if last_extracted_text else None) or 'Задача выполнена'
                    log.success(f"✅ Задача завершена: {final_result}")
                    await self._emit({"type": "agent_message", "role": "assistant", "text": f"✅ {final_result}"})
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
                await self._emit({"type": "agent_message", "role": "system", "text": f"Результат: {'ok' if result.success else 'error'}"})

                # Запоминаем последний извлечённый текст, чтобы потом можно было вернуть его как итог
                if action_type == ActionType.EXTRACT_TEXT and result.success and isinstance(result.data, str) and result.data.strip():
                    last_extracted_text = result.data
                
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
            if task_completed:
                self.status = TaskStatus.COMPLETED
                return {
                    'success': True,
                    'result': final_result or 'Задача выполнена',
                    'steps': self.current_step
                }

            if self.current_step >= config.MAX_STEPS:
                log.warning(f"Достигнут лимит шагов: {config.MAX_STEPS}")
                self.status = TaskStatus.FAILED
                return {
                    'success': False,
                    'result': 'Превышен лимит шагов',
                    'steps': self.current_step
                }

            # Если вышли из цикла без task_complete и без явной ошибки — считаем это провалом
            self.status = TaskStatus.FAILED
            return {
                'success': False,
                'result': f"Задача не завершена (нет task_complete). Последний ответ модели: {last_llm_message[:500]}",
                'steps': self.current_step
            }
            
        except asyncio.CancelledError:
            log.warning("Задача отменена (CancelledError)")
            self.status = TaskStatus.FAILED
            return {
                'success': False,
                'result': 'Task cancelled',
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
            if config.KEEP_BROWSER_OPEN:
                log.info("Браузер оставлен открытым (KEEP_BROWSER_OPEN=true)")
            else:
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
