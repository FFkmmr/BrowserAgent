# 🎨 ВИЗУАЛЬНАЯ СТРУКТУРА ПРОЕКТА

```
browser-agent/
│
├── 📦 src/                           # Python Backend
│   │
│   ├── 🧠 core/                      # ЯДРО АГЕНТА
│   │   ├── orchestrator.py           # 🎯 Главный координатор
│   │   │   └─> AgentOrchestrator    # - run_task()
│   │   │                             # - pause_task()
│   │   │                             # - get_status()
│   │   │
│   │   └── execution_loop.py         # 🔄 Цикл выполнения (ReAct)
│   │       └─> ExecutionLoop        # - execute_task()
│   │           │                     # - Observe → Reason → Act
│   │           └─> Цикл до MAX_STEPS
│   │
│   ├── 🤖 ai/                        # AI ИНТЕГРАЦИЯ
│   │   ├── llm_client.py             # 💬 Claude API клиент
│   │   │   └─> ClaudeClient         # - get_next_action()
│   │   │                             # - Tool calling
│   │   │                             # - Token management
│   │   │
│   │   ├── prompts.py                # 📝 Промпты
│   │   │   ├─> SYSTEM_PROMPT        # Инструкции агента
│   │   │   ├─> build_task_prompt()
│   │   │   └─> build_observation()
│   │   │
│   │   └── tools.py                  # 🔧 Tool Definitions
│   │       └─> get_tool_definitions() # JSON схемы для Claude
│   │
│   ├── 🌐 browser/                   # АВТОМАТИЗАЦИЯ БРАУЗЕРА
│   │   ├── browser_controller.py    # 🎮 Playwright manager
│   │   │   └─> BrowserController    # - start() / close()
│   │   │                             # - Browser lifecycle
│   │   │
│   │   ├── page_analyzer.py          # 🔍 Анализ страниц
│   │   │   └─> PageAnalyzer         # - analyze() → PageState
│   │   │                             # - Simplify DOM
│   │   │                             # - Extract elements
│   │   │
│   │   └── actions.py                # ⚡ Библиотека действий
│   │       └─> BrowserActions       # - navigate(), click()
│   │           ├─ Navigation        # - type(), extract()
│   │           ├─ Interaction       # - scroll(), select()
│   │           ├─ Extraction
│   │           └─ Waiting
│   │
│   ├── 💾 context/                   # УПРАВЛЕНИЕ ПАМЯТЬЮ
│   │   └── memory.py                 # 🧩 Context Manager
│   │       ├─> AgentMemory          # - История шагов
│   │       │   └─ steps_history[]   # - Текущая задача
│   │       │
│   │       └─> ContextManager       # - build_messages_for_llm()
│   │           ├─ Short-term        # - Token optimization
│   │           └─ Working memory
│   │
│   └── 🛠️ utils/                     # УТИЛИТЫ
│       ├── types.py                  # 📋 Типы данных
│       │   ├─> TaskStatus (Enum)
│       │   ├─> ActionType (Enum)
│       │   ├─> Action (Dataclass)
│       │   ├─> ActionResult
│       │   ├─> PageState
│       │   └─> AgentStep
│       │
│       ├── logger.py                 # 📊 Логирование
│       │   └─> setup_logger()       # Loguru config
│       │
│       └── dom_utils.py              # 🌳 DOM утилиты
│           ├─> simplify_dom()       # Упрощение HTML
│           ├─> extract_elements()   # Поиск интерактивных
│           └─> generate_selector()  # Умные селекторы
│
├── 🎨 extension/                     # Chrome Extension
│   ├── manifest.json                 # ⚙️ Манифест V3
│   │
│   ├── background.js                 # 🔌 Service Worker
│   │   ├─> connectToBackend()       # WebSocket к Python
│   │   ├─> handleMessages()         # Координация
│   │   └─> agentState{}             # Состояние
│   │
│   ├── content.js                    # 📄 Content Script
│   │   ├─> executeAction()          # Выполнение в DOM
│   │   ├─> analyzePage()            # Анализ элементов
│   │   └─> highlightElement()       # Визуализация
│   │
│   ├── popup/                        # 🪟 Popup UI
│   │   ├── popup.html               # HTML интерфейс
│   │   └── popup.js                 # Управление UI
│   │
│   └── icons/                        # 🎯 Иконки
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
├── ⚙️ config/                        # КОНФИГУРАЦИЯ
│   └── config.py                     # 🔧 Настройки
│       └─> Config
│           ├─ ANTHROPIC_API_KEY
│           ├─ MAX_STEPS = 50
│           ├─ MODEL_NAME
│           └─ HEADLESS, TIMEOUT
│
├── 📚 examples/                      # ПРИМЕРЫ
│   ├── example_tasks.py              # Готовые задачи
│   └── interactive_agent.py          # Интерактивный режим
│
├── 📖 docs/                          # ДОКУМЕНТАЦИЯ
│   └── ARCHITECTURE.md               # Подробная архитектура
│
├── 🚀 main.py                        # ТОЧКА ВХОДА
│   └─> async main()                 # Запуск агента
│       └─> AgentOrchestrator
│
├── 📦 requirements.txt               # Python зависимости
├── 🔐 .env.example                   # Шаблон переменных
├── 📝 .gitignore
└── 📄 README.md                      # Документация


═══════════════════════════════════════════════════════════════

🔄 EXECUTION FLOW (Поток выполнения)

1️⃣  USER
    ↓ "Найди на Wikipedia статью про Python"
    
2️⃣  ORCHESTRATOR
    ↓ Инициализация → Запуск ExecutionLoop
    
3️⃣  EXECUTION LOOP (Цикл)
    │
    ├─→ 📊 Page Analyzer
    │   └─→ PageState (URL, DOM, элементы)
    │
    ├─→ 💾 Context Manager
    │   └─→ Messages для LLM
    │
    ├─→ 🤖 Claude Client
    │   ├─ Reasoning: "Нужно открыть Wikipedia"
    │   └─→ Tool Call: navigate(url="...")
    │
    ├─→ ⚡ Browser Actions
    │   └─→ Выполнение действия
    │
    ├─→ 💾 Memory Update
    │   └─→ Сохранение шага
    │
    └─→ ✅ Check: Completed? → if No, repeat
    
4️⃣  RESULT
    └─→ USER: "✅ Задача выполнена: Найдена статья про Python"


═══════════════════════════════════════════════════════════════

📊 СТАТИСТИКА ПРОЕКТА

Python файлов:     ~15 основных
Строк кода:        ~2000+
Модулей:           5 основных (core, ai, browser, context, utils)
Tools:             10 действий для агента
Dependencies:      ~10 пакетов

Архитектура:       Модульная, расширяемая
Паттерн:           ReAct (Reasoning + Acting)
Async:             100% асинхронный код
Type Safety:       Полная типизация (Python 3.9+)

═══════════════════════════════════════════════════════════════
```

## 🎯 Ключевые особенности архитектуры

### ✅ Модульность
Каждый компонент независим и может быть заменён

### ✅ Расширяемость  
Легко добавлять новые действия, LLM провайдеры, типы анализа

### ✅ Тестируемость
Чёткое разделение ответственности, mock'и для тестов

### ✅ Поддерживаемость
Понятная структура, подробные комментарии, документация

### ✅ Production-ready
Логирование, обработка ошибок, graceful shutdown
