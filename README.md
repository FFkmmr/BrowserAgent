# 🤖 AI Browser Agent

> Интеллектуальный AI-агент, способный автономно управлять веб-браузером для выполнения сложных многошаговых задач на основе естественных языковых команд.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-green.svg)](https://playwright.dev/)
[![Claude](https://img.shields.io/badge/Claude-3.5_Sonnet-purple.svg)](https://www.anthropic.com/)

## 🎯 Возможности

- 🧠 **Автономное принятие решений** - агент сам планирует и выполняет действия
- 🔄 **ReAct паттерн** - наблюдение → рассуждение → действие → рефлексия
- 🌐 **Полная автоматизация браузера** - клики, ввод текста, навигация, извлечение данных
- 💬 **Естественный язык** - описывайте задачи обычными словами
- 🎨 **Chrome Extension** - удобный интерфейс прямо в браузере
- 🔧 **Расширяемая архитектура** - легко добавлять новые действия и функции

## 📋 Примеры задач

```python
# Поиск и извлечение информации
"Открой Wikipedia, найди статью про Python и извлеки первый абзац"

# Исследование данных
"Перейди на HackerNews и собери заголовки топ-10 статей"

# Многошаговые задачи
"Открой GitHub, найди репозитории по AI automation, отсортируй по звёздам и покажи первые 5"
```

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│          Chrome Extension               │
│         (User Interface)                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       Agent Orchestrator                │
│    (Task Coordination)                  │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌─────────────┐ ┌─────────────┐
│ AI Engine   │ │ Browser     │
│ (Claude)    │ │ (Playwright)│
└─────────────┘ └─────────────┘
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Установка пакетов
pip install -r requirements.txt

# Установка браузеров для Playwright
python -m playwright install chromium
```

### 2. Настройка

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Настройте LLM провайдера через `API_KEY`, `API_BASE_URL`, `MODEL_NAME`.

Пример для Groq (OpenAI-compatible):

```env
API_KEY=gsk_...
API_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.3-70b-versatile
```

### 3. Запуск

**Вариант A: Простой скрипт**

```bash
python main.py
```

**Вариант B: Интерактивный режим**

```bash
python examples/interactive_agent.py
```

**Вариант C: Chrome Extension**

1. Откройте Chrome
2. Перейдите в `chrome://extensions/`
3. Включите "Режим разработчика"
4. Нажмите "Загрузить распакованное расширение"
5. Выберите папку `extension/`

## 📁 Структура проекта

```
browser-agent/
├── src/                      # Исходный код Python
│   ├── core/                 # Ядро агента
│   │   ├── orchestrator.py   # Главный координатор
│   │   └── execution_loop.py # Цикл выполнения (ReAct)
│   ├── ai/                   # AI интеграция
│   │   ├── llm_client.py     # Claude API клиент
│   │   ├── prompts.py        # Промпты
│   │   └── tools.py          # Tool definitions
│   ├── browser/              # Автоматизация браузера
│   │   ├── browser_controller.py
│   │   ├── page_analyzer.py
│   │   └── actions.py
│   ├── context/              # Управление контекстом
│   │   └── memory.py
│   └── utils/                # Утилиты
│       ├── types.py
│       ├── logger.py
│       └── dom_utils.py
├── extension/                # Chrome Extension
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   └── popup/
├── config/                   # Конфигурация
├── examples/                 # Примеры использования
├── docs/                     # Документация
├── main.py                   # Точка входа
└── requirements.txt
```

## 🎓 Как это работает

### ReAct Pattern (Reasoning + Acting)

Агент работает в цикле:

```python
while не_выполнено:
    # 1. PERCEPTION - Анализ страницы
    page_state = analyze_current_page()
  
    # 2. REASONING - Запрос к Claude
    decision = claude.decide_next_action(
        task=user_task,
        current_state=page_state,
        history=previous_steps
    )
  
    # 3. ACTION - Выполнение
    result = execute_action(decision)
  
    # 4. REFLECTION - Оценка результата
    if task_completed:
        break
```

### Пример выполнения

**Задача:** "Найди на Wikipedia статью про Python"

```
ШАГ 1:
  Observation: Вижу пустую страницу
  Thought: Нужно открыть Wikipedia
  Action: navigate(url="https://wikipedia.org")
  ✓ Успешно

ШАГ 2:
  Observation: Вижу главную страницу Wikipedia с полем поиска
  Thought: Нужно ввести "Python" в поиск
  Action: type_text(selector="input[name='search']", text="Python")
  ✓ Успешно

ШАГ 3:
  Observation: Текст введён
  Thought: Нужно нажать кнопку поиска
  Action: click(selector="button[type='submit']")
  ✓ Успешно

ШАГ 4:
  Observation: Открылась страница с результатами
  Thought: Вижу статью про Python programming language
  Action: click(selector="a[title='Python (programming language)']")
  ✓ Успешно

ШАГ 5:
  Observation: Открыта статья про Python
  Thought: Задача выполнена
  Action: task_complete(result="Найдена и открыта статья про Python")
  ✅ Задача завершена
```

## 🔧 Конфигурация

### config/config.py

```python
class Config:
    # API Keys
    ANTHROPIC_API_KEY: str
  
    # Agent Settings
    MAX_STEPS: int = 50              # Макс. шагов
    TIMEOUT_SECONDS: int = 300       # Тайм-аут
  
    # Browser
    HEADLESS: bool = False           # Показывать браузер
    SLOW_MO: int = 100               # Замедление (мс)
  
    # LLM
    MODEL_NAME: str = "claude-3-5-sonnet-20241022"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
```

## 📚 API Reference

### AgentOrchestrator

```python
from src.core.orchestrator import AgentOrchestrator

agent = AgentOrchestrator()

# Выполнить задачу
result = await agent.run_task("Описание задачи")

# Результат
{
    'success': True,
    'result': 'Описание выполненной задачи',
    'steps': 5
}
```

### Доступные действия (Tools)

| Tool              | Описание               | Параметры              |
| ----------------- | ------------------------------ | ------------------------------- |
| `navigate`      | Переход по URL        | `url: str`                    |
| `click`         | Клик по элементу | `selector: str`               |
| `type_text`     | Ввод текста          | `selector: str, text: str`    |
| `extract_text`  | Извлечь текст      | `selector: str`               |
| `scroll`        | Прокрутка             | `direction: str, amount: int` |
| `select_option` | Выбор в dropdown         | `selector: str, value: str`   |
| `wait`          | Ожидание               | `milliseconds: int`           |
| `go_back`       | Назад                     | -                               |
| `reload`        | Перезагрузка       | -                               |

## 🐛 Отладка

### Логи

Логи сохраняются в `logs/agent.log`:

```bash
# Просмотр в реальном времени
tail -f logs/agent.log
```

### Режим отладки

```python
# В .env
LOG_LEVEL=DEBUG
HEADLESS=false
SLOW_MO=500  # Замедлить действия
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch
3. Commit изменения
4. Push в branch
5. Создайте Pull Request

## 📝 TODO

- [ ] Поддержка скриншотов для Vision API
- [ ] Сохранение истории задач в БД
- [ ] WebSocket сервер для Extension
- [ ] Поддержка множественных вкладок
- [ ] Обработка капч и авторизации
- [ ] Планирование многошаговых задач

## ⚠️ Ограничения

- **Не использовать для:**

  - Финансовых транзакций без подтверждения
  - Отправки сообщений от вашего имени
  - Действий, требующих капчу
- **Текущие ограничения:**

  - Работает только с одной вкладкой
  - Не поддерживает iframe navigation
  - Требует явного описания задачи

## 📄 Лицензия

MIT License - см. LICENSE файл

## 👨‍💻 Автор

FFkmmr - [GitHub](https://github.com/FFkmmr)

## 🙏 Благодарности

- [Anthropic Claude](https://www.anthropic.com/) - AI модель
- [Playwright](https://playwright.dev/) - Browser automation
- [Loguru](https://github.com/Delgan/loguru) - Logging

---

**Создано с ❤️ для автоматизации рутинных задач в браузере**
