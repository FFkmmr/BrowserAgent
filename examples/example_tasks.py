"""
Примеры задач для AI Browser Agent
"""

EXAMPLE_TASKS = {
    "simple_search": """
        Открой Google (https://google.com), 
        найди информацию про Python programming language,
        и открой первую ссылку.
    """,
    
    "wikipedia_research": """
        Перейди на Wikipedia (https://wikipedia.org),
        найди статью про Machine Learning,
        извлеки определение из первого абзаца.
    """,
    
    "github_search": """
        Открой GitHub (https://github.com),
        найди репозитории по запросу "AI browser automation",
        и покажи названия первых 5 репозиториев.
    """,
    
    "form_filling": """
        Открой страницу https://example.com/contact,
        заполни форму обратной связи:
        - Имя: Test User
        - Email: test@example.com
        - Сообщение: Testing AI Browser Agent
        НО НЕ ОТПРАВЛЯЙ ФОРМУ!
    """,
    
    "data_extraction": """
        Открой сайт новостей (например, https://news.ycombinator.com),
        извлеки заголовки первых 10 статей.
    """,
}


# Для импорта
def get_example_task(name: str) -> str:
    """Получить пример задачи по имени"""
    return EXAMPLE_TASKS.get(name, "").strip()
