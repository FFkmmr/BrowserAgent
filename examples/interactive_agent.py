"""
Пример интерактивного использования агента
"""
import asyncio
from src.core.orchestrator import AgentOrchestrator
from src.utils.logger import log


async def interactive_mode():
    """Интерактивный режим работы с агентом"""
    
    agent = AgentOrchestrator()
    
    print("\n" + "="*60)
    print("🤖 AI BROWSER AGENT - Интерактивный режим")
    print("="*60)
    print("Введите задачу на естественном языке.")
    print("Для выхода введите 'exit' или 'quit'\n")
    
    while True:
        try:
            # Получение задачи от пользователя
            print("\n" + "-"*60)
            task = input("📝 Ваша задача: ").strip()
            
            if not task:
                continue
            
            if task.lower() in ['exit', 'quit', 'q']:
                print("👋 До свидания!")
                break
            
            # Выполнение задачи
            print(f"\n🚀 Начинаю выполнение...\n")
            result = await agent.run_task(task)
            
            # Вывод результата
            print("\n" + "="*60)
            if result['success']:
                print("✅ ЗАДАЧА ВЫПОЛНЕНА УСПЕШНО!")
                print(f"\n📊 Результат:\n{result['result']}")
            else:
                print("❌ ЗАДАЧА НЕ ВЫПОЛНЕНА")
                print(f"\n⚠️ Причина:\n{result['result']}")
            
            print(f"\n📈 Шагов выполнено: {result.get('steps', 0)}")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⏸️  Задача прервана. Начните новую задачу или введите 'exit'")
            continue
        except Exception as e:
            log.error(f"Ошибка: {e}")
            continue


if __name__ == "__main__":
    try:
        asyncio.run(interactive_mode())
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
