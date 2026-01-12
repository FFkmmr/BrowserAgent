"""
AI Browser Agent - Главный файл запуска

Пример использования:
    python main.py
"""
import asyncio
from src.core.orchestrator import AgentOrchestrator
from src.utils.logger import log


async def main():
    """Главная функция"""
    
    # Создание агента
    agent = AgentOrchestrator()
    
    # Пример задачи
    task = """
    Открой сайт Wikipedia (https://wikipedia.org), 
    найди статью про искусственный интеллект (Artificial Intelligence),
    и извлеки первый абзац статьи.
    """
    
    log.info("Запуск агента с задачей...")
    
    # Выполнение задачи
    result = await agent.run_task(task)
    
    # Вывод результата
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТ ВЫПОЛНЕНИЯ:")
    print("="*60)
    print(f"Успех: {result['success']}")
    print(f"Результат: {result['result']}")
    print(f"Шагов выполнено: {result.get('steps', 0)}")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("\nВыполнение прервано пользователем")
    except Exception as e:
        log.error(f"Критическая ошибка: {e}", exc_info=True)
