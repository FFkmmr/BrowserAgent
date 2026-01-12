"""
Управление памятью и контекстом агента
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from src.utils.types import AgentStep
from src.utils.logger import log


@dataclass
class AgentMemory:
    """Память агента о текущей задаче"""
    task_description: str
    steps_history: List[AgentStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: AgentStep):
        """Добавить шаг в историю"""
        self.steps_history.append(step)
        log.debug(f"Шаг {step.step_number} добавлен в память")
    
    def get_recent_steps(self, count: int = 5) -> List[AgentStep]:
        """Получить последние N шагов"""
        return self.steps_history[-count:] if self.steps_history else []
    
    def get_step_count(self) -> int:
        """Количество выполненных шагов"""
        return len(self.steps_history)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для логов"""
        return {
            'task': self.task_description,
            'steps_count': len(self.steps_history),
            'created_at': self.created_at.isoformat()
        }


class ContextManager:
    """Управление контекстом для LLM"""
    
    def __init__(self):
        self.memory: AgentMemory = None
        self.current_page_state: Dict[str, Any] = {}
    
    def initialize_task(self, task_description: str):
        """Инициализировать новую задачу"""
        self.memory = AgentMemory(task_description=task_description)
        log.info(f"Инициализирована новая задача: {task_description[:100]}")
    
    def update_page_state(self, page_state: Dict[str, Any]):
        """Обновить состояние страницы"""
        self.current_page_state = page_state
        log.debug(f"Обновлено состояние страницы: {page_state.get('url', 'unknown')}")
    
    def add_step(self, step: AgentStep):
        """Добавить выполненный шаг"""
        if self.memory:
            self.memory.add_step(step)
    
    def build_messages_for_llm(self, include_page_state: bool = True) -> List[Dict[str, Any]]:
        """
        Построить список сообщений для отправки в LLM
        Формат Claude: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        messages = []
        
        if not self.memory:
            return messages
        
        # Первое сообщение - задача пользователя
        from src.ai.prompts import build_task_prompt
        task_prompt = build_task_prompt(self.memory.task_description)
        
        # Добавляем текущее состояние страницы
        if include_page_state and self.current_page_state:
            from src.ai.prompts import build_observation_prompt
            
            history_for_prompt = [
                {
                    'step_number': s.step_number,
                    'action': {'type': s.action.type.value},
                    'result': {'success': s.result.success}
                }
                for s in self.memory.get_recent_steps(3)
            ]
            
            observation_prompt = build_observation_prompt(
                self.current_page_state,
                self.memory.get_step_count() + 1,
                history_for_prompt
            )
            
            task_prompt += "\n\n" + observation_prompt
        
        messages.append({
            "role": "user",
            "content": task_prompt
        })
        
        # Добавляем историю взаимодействий (последние 5 шагов)
        recent_steps = self.memory.get_recent_steps(5)
        
        for step in recent_steps:
            # Ответ ассистента (thinking + tool call)
            assistant_content = []
            
            # Добавляем reasoning как текст
            if step.thought:
                assistant_content.append({
                    "type": "text",
                    "text": step.thought
                })
            
            # Добавляем tool call
            assistant_content.append({
                "type": "tool_use",
                "id": f"step_{step.step_number}",
                "name": step.action.type.value,
                "input": step.action.parameters
            })
            
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Результат выполнения tool
            result_content = {
                "success": step.result.success,
                "data": step.result.data,
            }
            
            if step.result.error:
                result_content["error"] = step.result.error
            
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": f"step_{step.step_number}",
                    "content": str(result_content)
                }]
            })
        
        return messages
    
    def get_context_size_estimate(self) -> int:
        """Оценка размера контекста в токенах (приблизительно)"""
        # Грубая оценка: 1 токен ≈ 4 символа
        total_chars = len(str(self.memory.to_dict())) + len(str(self.current_page_state))
        return total_chars // 4
    
    def should_compress_context(self) -> bool:
        """Нужно ли сжимать контекст?"""
        from config.config import config
        return self.get_context_size_estimate() > config.CONTEXT_COMPRESSION_THRESHOLD
    
    def clear(self):
        """Очистить контекст"""
        self.memory = None
        self.current_page_state = {}
        log.info("Контекст очищен")
