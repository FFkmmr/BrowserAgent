"""
Типы данных для AI Browser Agent
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class TaskStatus(Enum):
    """Статусы выполнения задачи"""
    IDLE = "idle"
    PARSING = "parsing"
    EXECUTING = "executing"
    WAITING_USER_INPUT = "waiting_user_input"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ActionType(Enum):
    """Типы действий в браузере"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    SCROLL = "scroll"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_DATA = "extract_data"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    RELOAD = "reload"


@dataclass
class Action:
    """Действие агента"""
    type: ActionType
    parameters: Dict[str, Any]
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ActionResult:
    """Результат выполнения действия"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class PageState:
    """Состояние веб-страницы"""
    url: str
    title: str
    simplified_dom: str
    interactive_elements: List[Dict[str, Any]]
    screenshot_path: Optional[str] = None


@dataclass
class Task:
    """Задача для агента"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentStep:
    """Один шаг выполнения агента (ReAct pattern)"""
    step_number: int
    observation: str  # Что видит агент
    thought: str      # Рассуждение агента
    action: Action    # Действие
    result: ActionResult  # Результат
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolDefinition:
    """Определение tool для LLM"""
    name: str
    description: str
    input_schema: Dict[str, Any]
