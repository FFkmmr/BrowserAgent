"""
Клиент для работы с LLM API (OpenAI-compatible, z.ai, Claude и др.)
"""
from typing import List, Dict, Any, Optional
import json
import re
import ast
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

    @staticmethod
    def _estimate_tokens_rough(text: str) -> int:
        """Очень грубая оценка токенов: 1 токен ≈ 4 символа."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
        """Пытается извлечь JSON-объект из текста (на случай, если модель вернёт JSON без tool calling)."""
        if not text:
            return None

        # Сначала пробуем как чистый JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Затем пытаемся вырезать первый {...} блок
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None

        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _parse_model_action_from_text(self, content: str) -> Dict[str, Any]:
        """Fallback парсер.

        Поддерживает:
        1) JSON: {"name": "navigate", "input": {...}}
        2) ReAct текст: "Action: navigate(url=\"https://...\")"
        """

        # 1) JSON
        parsed = self._extract_json_object(content)
        if parsed:
            name = parsed.get('name') or parsed.get('tool') or parsed.get('action')
            tool_input = parsed.get('input') or parsed.get('parameters') or parsed.get('args') or {}

            tool_calls = []
            if isinstance(name, str) and isinstance(tool_input, dict):
                tool_calls.append({'id': 'fallback_0', 'name': name, 'input': tool_input})

            return {
                'thinking': parsed.get('thinking') or parsed.get('thought') or (content or ''),
                'tool_calls': tool_calls,
                'message': content or '',
                'stop_reason': 'fallback_json'
            }

        # 2) ReAct: ищем строку Action:
        # Пример: Action: navigate(url="https://wikipedia.org")
        action_match = re.search(r"^\s*Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*$", content or "", re.MULTILINE)
        if action_match:
            tool_name = action_match.group(1)
            args_str = action_match.group(2).strip()

            # Парсим kwargs через ast (без eval): f(a="x", b=1)
            tool_input: Dict[str, Any] = {}
            try:
                expr = ast.parse(f"f({args_str})", mode="eval")
                if isinstance(expr.body, ast.Call):
                    for kw in expr.body.keywords:
                        if kw.arg is None:
                            continue
                        tool_input[kw.arg] = ast.literal_eval(kw.value)
            except Exception:
                tool_input = {}

            return {
                'thinking': content or '',
                'tool_calls': [{'id': 'fallback_0', 'name': tool_name, 'input': tool_input}],
                'message': content or '',
                'stop_reason': 'fallback_react'
            }

        return {
            'thinking': content or '',
            'tool_calls': [],
            'message': content or '',
            'stop_reason': 'fallback_no_action'
        }

    @staticmethod
    def _action_json_instruction() -> str:
        return (
            "Ответь ТОЛЬКО валидным JSON-объектом (без Markdown/пояснений). "
            "Схема: {\"name\": \"<tool_name>\", \"input\": { ... }, \"thinking\": \"...\"}. "
            "<tool_name> один из: navigate, click, type_text, extract_text, scroll, "
            "select_option, wait, go_back, reload, task_complete. "
            "Если нужно завершить задачу — используй task_complete с полем result."
        )

    async def _completion_json_mode(self, messages: List[Dict[str, Any]], max_tokens: int) -> Any:
        """Запрос в JSON-mode (если провайдер поддерживает response_format=json_object)."""
        return await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=config.TEMPERATURE,
            messages=messages,
            response_format={"type": "json_object"},
        )

    async def _repair_json_once(self, base_messages: List[Dict[str, Any]], bad_text: str, max_tokens: int) -> str:
        """Один короткий запрос: починить JSON и вернуть только JSON."""
        repair_messages = list(base_messages)
        repair_messages.append({
            "role": "user",
            "content": (
                "Твой прошлый ответ не является валидным JSON. "
                "Преобразуй его в валидный JSON по схеме и верни ТОЛЬКО JSON.\n\n"
                f"ПРОШЛЫЙ ОТВЕТ:\n{bad_text}"
            )
        })
        resp = await self._completion_json_mode(repair_messages, max_tokens=max_tokens)
        return resp.choices[0].message.content or ""

    @staticmethod
    def _extract_provider_error_message(exc: Exception) -> Optional[str]:
        """Пытается вытащить текст ошибки провайдера из Exception.

        Например openai SDK часто форматирует так:
        "Error code: 429 - {'error': {'code': '1113', 'message': '...'}}"
        """
        text = str(exc) if exc else ""
        if not text:
            return None

        # Пытаемся достать словарь после " - "
        if " - " in text:
            _, tail = text.split(" - ", 1)
            tail = tail.strip()
            try:
                parsed = ast.literal_eval(tail)
                if isinstance(parsed, dict):
                    err = parsed.get("error")
                    if isinstance(err, dict):
                        msg = err.get("message")
                        return msg if isinstance(msg, str) and msg else None
            except Exception:
                pass

        # Фолбэк по подстрокам
        if "余额不足" in text:
            return "余额不足或无可用资源包,请充值。 (BigModel: недостаточно баланса/нет доступного пакета)"
        return None

    @staticmethod
    def _is_fatal_provider_error_message(message: str) -> bool:
        """Определяет, стоит ли прекращать попытки (нет смысла делать fallback).

        Фатальные случаи: нет денег/квоты, невалидный ключ, нет доступа/модель не найдена.
        Нефатальные: tool calling не сработал, формат ответа не тот и т.п.
        """
        if not message:
            return False

        m = message.lower()
        fatal_markers = [
            "insufficient",
            "quota",
            "rate limit",
            "billing",
            "balance",
            "unauthorized",
            "authentication",
            "invalid api key",
            "forbidden",
            "model_not_found",
            "not found",
            "no permission",
            "余额不足",
            "请充值",
        ]
        return any(marker in m for marker in fatal_markers)
    
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

            # Оценка размера контекста (грубо)
            total_chars = 0
            for m in openai_messages:
                c = m.get('content')
                if isinstance(c, str):
                    total_chars += len(c)
            log.debug(
                f"Размер prompt: ~{total_chars} chars (~{self._estimate_tokens_rough('x' * total_chars)} tokens rough)"
            )

            # --- ПРЕДПОЧТИТАЕМ ДЕТЕРМИНИРОВАННЫЙ JSON-MODE ---
            # Это надёжнее, чем tool calling / тег <function=...>, и одинаково работает с большинством OpenAI-compatible API.
            json_mode_messages = list(openai_messages)
            json_mode_messages.append({"role": "user", "content": self._action_json_instruction()})

            try:
                response = await self._completion_json_mode(
                    json_mode_messages,
                    max_tokens=max_tokens or config.MAX_TOKENS,
                )
            except Exception as json_mode_exc:
                # Если провайдер не поддерживает response_format/json-mode — падаем обратно на tools.
                log.warning(f"JSON-mode не сработал ({json_mode_exc}). Пробуем tools/fallback.")

                # Вызов API (с tools). Некоторые OpenAI-compatible провайдеры могут падать на tool calling.
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        max_tokens=max_tokens or config.MAX_TOKENS,
                        temperature=config.TEMPERATURE,
                        messages=openai_messages,
                        tools=self.tools if self.tools else None,
                        tool_choice="auto" if self.tools else None
                    )
                except Exception as tool_exc:
                    provider_msg = self._extract_provider_error_message(tool_exc)
                    if provider_msg and self._is_fatal_provider_error_message(provider_msg):
                        raise RuntimeError(f"LLM provider error: {provider_msg}")

                    # Fallback: повторяем запрос без tools и просим JSON-ответ с действием.
                    log.warning(
                        f"LLM запрос с tools завершился ошибкой ({tool_exc}). Повторяем без tools с JSON-инструкцией."
                    )

                    fallback_messages = list(openai_messages)
                    fallback_messages.append({
                        "role": "user",
                        "content": self._action_json_instruction()
                    })

                    try:
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            max_tokens=max_tokens or config.MAX_TOKENS,
                            temperature=config.TEMPERATURE,
                            messages=fallback_messages,
                        )
                    except Exception as fallback_exc:
                        provider_msg = self._extract_provider_error_message(fallback_exc) or self._extract_provider_error_message(tool_exc)
                        if provider_msg and self._is_fatal_provider_error_message(provider_msg):
                            raise RuntimeError(f"LLM provider error: {provider_msg}")
                        raise RuntimeError(f"LLM request failed. Original error: {tool_exc}. Fallback error: {fallback_exc}")
            
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
            else:
                # Если tool_calls нет (например, fallback без tools), пробуем распарсить JSON из content
                parsed_fallback = self._parse_model_action_from_text(message.content or '')

                # Если JSON-mode вернул невалидный JSON (или мусор), пробуем один раз "починить" JSON.
                if not parsed_fallback.get('tool_calls'):
                    try:
                        repaired = await self._repair_json_once(
                            base_messages=openai_messages,
                            bad_text=message.content or "",
                            max_tokens=min(512, max_tokens or config.MAX_TOKENS),
                        )
                        parsed_fallback = self._parse_model_action_from_text(repaired)
                    except Exception:
                        pass

                if parsed_fallback.get('tool_calls'):
                    result['tool_calls'] = parsed_fallback['tool_calls']
                    if parsed_fallback.get('thinking'):
                        result['thinking'] = parsed_fallback['thinking']
                    result['stop_reason'] = parsed_fallback.get('stop_reason', result['stop_reason'])
            
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
