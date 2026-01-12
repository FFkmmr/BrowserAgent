"""
Клиент для работы с LLM API (OpenAI-compatible, z.ai, Claude и др.)
"""
from typing import List, Dict, Any, Optional
import json
from openai import AsyncOpenAI
from config.config import config
from src.utils.logger import log
from src.ai.tools import get_tool_definitions
from src.ai.prompts import SYSTEM_PROMPT


class LLMClient:
    """Универсальный клиент для взаимодействия с LLM API"""
    
    def __init__(self):
        if not config.API_KEY:
            raise ValueError("API_KEY не установлен в .env файле")
        
        # Инициализация OpenAI-совместимого клиента
        self.client = AsyncOpenAI(
            api_key=config.API_KEY,
            base_url=config.API_BASE_URL
        )
        self.model = config.MODEL_NAME
        self.tools = self._convert_tools_to_openai_format(get_tool_definitions())
        
        log.info(f"LLM клиент инициализирован (модель: {self.model})")
        log.info(f"API endpoint: {config.API_BASE_URL}")
    
    def _convert_tools_to_openai_format(self, anthropic_tools: List[Dict]) -> List[Dict]:
        """Конвертация tool definitions из формата Anthropic в OpenAI"""
        openai_tools = []
        for tool in anthropic_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return openai_tools
    
    async def get_next_action(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Получить следующее действие от LLM
        
        Returns:
            {
                'thinking': str,  # Рассуждения модели
                'tool_calls': List[Dict],  # Вызовы tools
                'message': str  # Текстовый ответ
            }
        """
        try:
            log.debug(f"Запрос к LLM (messages: {len(messages)})")
            
            # Преобразуем messages для OpenAI формата (добавляем system prompt в начало)
            openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            
            for msg in messages:
                if msg["role"] == "user":
                    if isinstance(msg["content"], str):
                        openai_messages.append(msg)
                    else:
                        # Для tool_result преобразуем в текст
                        content_text = str(msg["content"])
                        openai_messages.append({
                            "role": "user",
                            "content": content_text
                        })
                elif msg["role"] == "assistant":
                    # Обрабатываем ответ ассистента
                    if isinstance(msg["content"], str):
                        openai_messages.append(msg)
                    else:
                        # Преобразуем из формата Anthropic
                        text_content = ""
                        for item in msg.get("content", []):
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_content += item.get("text", "")
                        if text_content:
                            openai_messages.append({
                                "role": "assistant",
                                "content": text_content
                            })
            
            # Вызов API
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens or config.MAX_TOKENS,
                temperature=config.TEMPERATURE,
                messages=openai_messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None
            )
            
            log.debug(f"Ответ получен. Finish reason: {response.choices[0].finish_reason}")
            
            # Парсим ответ
            choice = response.choices[0]
            message = choice.message
            
            result = {
                'thinking': message.content or '',
                'tool_calls': [],
                'message': message.content or '',
                'stop_reason': choice.finish_reason
            }
            
            # Обработка tool calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except:
                        arguments = {}
                    
                    result['tool_calls'].append({
                        'id': tool_call.id,
                        'name': tool_call.function.name,
                        'input': arguments
                    })
            
            # Логируем использование токенов
            if response.usage:
                log.info(f"Токены: input={response.usage.prompt_tokens}, output={response.usage.completion_tokens}")
            
            return result
            
        except Exception as e:
            log.error(f"Ошибка при запросе к LLM: {e}", exc_info=True)
            raise
    
    async def single_completion(self, prompt: str) -> str:
        """Простой запрос без tools (для вспомогательных задач)"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            log.error(f"Ошибка при single_completion: {e}")
            return ""
    
    def format_tool_result(self, tool_use_id: str, result: Any, is_error: bool = False) -> Dict:
        """Форматировать результат выполнения tool для отправки обратно в LLM"""
        return {
            "role": "user",
            "content": str(result)
        }


# Для обратной совместимости со старым кодом
ClaudeClient = LLMClient
