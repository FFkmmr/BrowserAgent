"""
Orchestrator - главный координатор агента
"""
from typing import Optional
from src.core.execution_loop import ExecutionLoop
from src.utils.logger import log
from config.config import config


class AgentOrchestrator:
    """
    Главный оркестратор AI Browser Agent
    Координирует работу всех компонентов
    """
    
    def __init__(self):
        log.info("Инициализация AI Browser Agent...")
        
        # Валидация конфигурации
        config.validate()
        
        self.execution_loop = ExecutionLoop()
        self.is_running = False
        
        log.success("Agent готов к работе!")
    
    async def run_task(self, task_description: str) -> dict:
        """
        Запустить выполнение задачи
        
        Args:
            task_description: Описание задачи на естественном языке
            
        Returns:
            dict: Результат выполнения
                {
                    'success': bool,
                    'result': str,
                    'steps': int
                }
        """
        if self.is_running:
            log.warning("Агент уже выполняет задачу")
            return {
                'success': False,
                'result': 'Агент уже занят выполнением другой задачи'
            }
        
        self.is_running = True
        
        try:
            result = await self.execution_loop.execute_task(task_description)
            return result
            
        finally:
            self.is_running = False
    
    async def pause_task(self):
        """Приостановить текущую задачу"""
        await self.execution_loop.pause()
    
    async def resume_task(self):
        """Возобновить приостановленную задачу"""
        await self.execution_loop.resume()
    
    def get_status(self) -> dict:
        """Получить текущий статус агента"""
        return {
            'is_running': self.is_running,
            'status': self.execution_loop.status.value,
            'current_step': self.execution_loop.current_step,
        }
