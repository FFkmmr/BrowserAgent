"""
Определения tools для Claude (function calling)
"""
from typing import List, Dict, Any


def get_tool_definitions() -> List[Dict[str, Any]]:
    """
    Возвращает список всех доступных tools для Claude
    """
    return [
        {
            "name": "navigate",
            "description": "Переход на указанный URL. Используй когда нужно открыть новую страницу.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Полный URL для перехода (например, https://google.com)"
                    }
                },
                "required": ["url"]
            }
        },
        {
            "name": "click",
            "description": "Клик по элементу на странице. Используй для нажатия кнопок, ссылок и других кликабельных элементов.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS селектор элемента для клика"
                    }
                },
                "required": ["selector"]
            }
        },
        {
            "name": "type_text",
            "description": "Ввод текста в поле ввода. Используй для заполнения форм.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS селектор input поля"
                    },
                    "text": {
                        "type": "string",
                        "description": "Текст для ввода"
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "Очистить поле перед вводом (по умолчанию true)",
                        "default": True
                    }
                },
                "required": ["selector", "text"]
            }
        },
        {
            "name": "extract_text",
            "description": "Извлечь текст с элемента или со всей страницы. Используй для чтения содержимого.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS селектор элемента (по умолчанию 'body' - вся страница)",
                        "default": "body"
                    }
                },
                "required": []
            }
        },
        {
            "name": "scroll",
            "description": "Прокрутка страницы в указанном направлении.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "top", "bottom"],
                        "description": "Направление прокрутки"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Количество пикселей для прокрутки (по умолчанию 500)",
                        "default": 500
                    }
                },
                "required": ["direction"]
            }
        },
        {
            "name": "select_option",
            "description": "Выбрать опцию в dropdown (select) элементе.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS селектор select элемента"
                    },
                    "value": {
                        "type": "string",
                        "description": "Значение опции для выбора"
                    }
                },
                "required": ["selector", "value"]
            }
        },
        {
            "name": "wait",
            "description": "Подождать указанное время. Используй когда нужно дать странице время на загрузку.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "milliseconds": {
                        "type": "integer",
                        "description": "Время ожидания в миллисекундах",
                        "default": 1000
                    }
                },
                "required": []
            }
        },
        {
            "name": "go_back",
            "description": "Вернуться на предыдущую страницу (кнопка 'Назад' в браузере).",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "reload",
            "description": "Перезагрузить текущую страницу.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "task_complete",
            "description": "Завершить задачу. Используй когда задача выполнена успешно.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "Описание результата выполнения задачи"
                    }
                },
                "required": ["result"]
            }
        }
    ]
