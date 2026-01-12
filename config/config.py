"""
Конфигурация AI Browser Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class Config:
    """Главная конфигурация агента"""
    
    # API Keys - Поддержка разных провайдеров
    API_KEY: str = os.getenv("API_KEY", "")  # Универсальный ключ
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")  # Для обратной совместимости
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.anthropic.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022")
    
    # Если API_KEY не задан, используем ANTHROPIC_API_KEY
    if not API_KEY and ANTHROPIC_API_KEY:
        API_KEY = ANTHROPIC_API_KEY
    
    # Agent Settings
    MAX_STEPS: int = int(os.getenv("MAX_STEPS", "50"))
    TIMEOUT_SECONDS: int = int(os.getenv("TIMEOUT_SECONDS", "300"))
    
    # Browser Settings
    BROWSER_TYPE: str = os.getenv("BROWSER_TYPE", "chromium")
    # Playwright 'channel' (e.g. 'chrome', 'msedge') to use system browser builds instead of bundled chromium
    BROWSER_CHANNEL: str = os.getenv("BROWSER_CHANNEL", "")
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"
    SLOW_MO: int = int(os.getenv("SLOW_MO", "100"))
    KEEP_BROWSER_OPEN: bool = os.getenv("KEEP_BROWSER_OPEN", "false").lower() == "true"

    # Attach to an existing Chrome/Chromium via DevTools (CDP)
    # Example: http://127.0.0.1:9222
    CHROME_CDP_URL: str = os.getenv("CHROME_CDP_URL", "")

    # CDP connection timeout (seconds). Used to fail fast when Chrome isn't
    # started with --remote-debugging-port.
    CDP_CONNECT_TIMEOUT_SECONDS: int = int(os.getenv("CDP_CONNECT_TIMEOUT_SECONDS", "5"))
    
    # LLM Settings (можно переопределить в .env)
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Context Management
    MAX_CONTEXT_LENGTH: int = 150000  # tokens
    CONTEXT_COMPRESSION_THRESHOLD: int = 100000
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = LOGS_DIR / os.getenv("LOG_FILE", "agent.log")
    
    # WebSocket (для связи с extension)
    WEBSOCKET_PORT: int = int(os.getenv("WEBSOCKET_PORT", "8765"))
    
    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        if not cls.API_KEY:
            raise ValueError("API_KEY не установлен в .env файле. Добавьте API_KEY=ваш-ключ")
        return True


# Singleton instance
config = Config()
