"""Run the extension backend WebSocket server.

Usage:
  venv\Scripts\python.exe run_backend.py

Then the Chrome extension connects to:
  ws://localhost:8765/ws

To control *your* Chrome (with your logged-in Gmail session), start Chrome with DevTools enabled
and set CHROME_CDP_URL in .env:
  CHROME_CDP_URL=http://127.0.0.1:9222
"""

import asyncio

from src.extension_backend.ws_server import run_server_forever


if __name__ == "__main__":
    asyncio.run(run_server_forever())
