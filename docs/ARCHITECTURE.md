# 📖 АРХИТЕКТУРА AI BROWSER AGENT

## Обзор системы

AI Browser Agent построен на принципах **Agentic AI** с использованием **ReAct паттерна** (Reasoning + Acting).

## Основные компоненты

### 1. Agent Core (`src/core/`)

**Orchestrator** - Главный координатор
- Управление жизненным циклом задач
- Инициализация компонентов
- Отслеживание статуса

**Execution Loop** - Цикл выполнения
- Реализует ReAct паттерн
- Координирует Perception → Reasoning → Action
- Управляет итерациями до завершения задачи

### 2. AI Integration (`src/ai/`)

**LLM Client** - Клиент для Claude API
- Асинхронные запросы к Claude
- Обработка tool calling
- Управление токенами

**Prompts** - Промпт-инжиниринг
- System prompt с инструкциями агента
- Dynamic prompts с контекстом
- Error recovery prompts

**Tools** - Определения функций
- JSON схемы для Claude function calling
- Описания всех доступных действий
- Валидация параметров

### 3. Browser Automation (`src/browser/`)

**Browser Controller** - Управление Playwright
- Запуск/закрытие браузера
- Управление контекстом и страницами
- Context manager для auto-cleanup

**Page Analyzer** - Анализ страниц
- Извлечение DOM структуры
- Упрощение для LLM
- Поиск интерактивных элементов
- Скриншоты (опционально)

**Actions** - Библиотека действий
- Navigation (navigate, back, forward, reload)
- Interaction (click, type, select, scroll)
- Extraction (extract_text, extract_data)
- Waiting (smart waits, timeouts)

### 4. Context Management (`src/context/`)

**Memory** - Управление памятью
- Short-term memory (текущая задача)
- История выполненных шагов
- Построение контекста для LLM
- Compression при необходимости

### 5. Utils (`src/utils/`)

**Types** - Типы данных
- Enums (TaskStatus, ActionType)
- Dataclasses (Action, ActionResult, PageState, etc.)
- Type hints для всего кода

**Logger** - Логирование
- Loguru с красивым форматированием
- Console + File output
- Разные уровни (DEBUG, INFO, WARNING, ERROR)

**DOM Utils** - Работа с DOM
- Упрощение HTML для LLM
- Генерация селекторов
- Извлечение интерактивных элементов

## Поток данных

```
User Input (Задача)
        ↓
Orchestrator.run_task()
        ↓
ExecutionLoop.execute_task()
        ↓
┌─────────────── ЦИКЛ ───────────────┐
│                                     │
│  1. Page Analyzer                  │
│     → analyze() → PageState        │
│                                     │
│  2. Context Manager                │
│     → build_messages_for_llm()     │
│                                     │
│  3. LLM Client                     │
│     → get_next_action()            │
│     → returns tool_call            │
│                                     │
│  4. Browser Actions                │
│     → execute(action) → Result     │
│                                     │
│  5. Memory                         │
│     → add_step()                   │
│                                     │
│  if not completed: repeat          │
└─────────────────────────────────────┘
        ↓
    Result → User
```

## ReAct Pattern Implementation

Каждая итерация цикла:

1. **Observation** (Наблюдение)
   - Анализ текущей страницы
   - Извлечение DOM, элементов, текста
   - Формирование PageState

2. **Thought** (Рассуждение)
   - Отправка контекста в Claude
   - LLM анализирует ситуацию
   - Выбор следующего действия

3. **Action** (Действие)
   - Выполнение выбранного tool
   - Взаимодействие с браузером
   - Получение результата

4. **Reflection** (Рефлексия)
   - Проверка успешности
   - Обновление памяти
   - Решение: продолжать или завершить?

## Tool Calling Flow

```python
# LLM возвращает
{
    "thinking": "Нужно кликнуть по кнопке поиска",
    "tool_calls": [
        {
            "name": "click",
            "input": {"selector": "button[type='submit']"}
        }
    ]
}

# Агент выполняет
result = await actions.execute(
    ActionType.CLICK,
    {"selector": "button[type='submit']"}
)

# Результат отправляется обратно в LLM
{
    "success": True,
    "data": {"clicked": True, "selector": "..."},
    "duration": 0.15
}
```

## Масштабирование

### Добавление нового действия

1. Добавить в `ActionType` enum
2. Создать метод в `BrowserActions`
3. Добавить tool definition в `tools.py`
4. Claude автоматически начнёт использовать

### Поддержка другого LLM

1. Создать новый клиент в `src/ai/`
2. Имплементировать тот же интерфейс
3. Переключить в orchestrator

### Расширение памяти

1. Добавить новые поля в `AgentMemory`
2. Обновить `build_messages_for_llm()`
3. Добавить compression логику

## Безопасность

- Blacklist опасных действий (в будущем)
- Ограничение количества шагов (MAX_STEPS)
- Timeout для задач
- Валидация user input
- Санитизация селекторов

## Performance

- Async/await везде
- Параллельное выполнение где возможно
- Context caching (Anthropic)
- Smart waits вместо sleep
- DOM simplification для экономии токенов

## Debugging

- Подробное логирование каждого шага
- Сохранение истории в память
- Screenshot capability
- Slow motion режим для отладки
