"""
AI Browser Agent - Главный файл запуска

Пример использования:
    python main.py
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from src.core.orchestrator import AgentOrchestrator
from src.utils.logger import log
from config.config import config


async def main():
    """Главная функция"""
    
    # Создание агента
    agent = AgentOrchestrator()
    
    # Пример задачи
    task = """хочу, чтобы ты на моей почте https://mail.google.com/mail/u/1/#inbox нашёл последнее приглашение меня на собеседование и дай инфу об этом приглашении"""
    
    log.info("Запуск агента с задачей...")
    
    # Выполнение задачи
    result = await agent.run_task(task)

    # Запись результата в файл рядом с логами
    try:
        results_path: Path = config.LOG_FILE.parent / "results.jsonl"
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "task": task.strip(),
            "success": bool(result.get("success")),
            "result": result.get("result"),
            "steps": result.get("steps"),
        }
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with results_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        log.info(f"Результат записан в файл: {results_path}")
    except Exception as e:
        log.warning(f"Не удалось записать результат в файл: {e}")
    
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
