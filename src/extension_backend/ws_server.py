"""WebSocket backend for the Chrome extension UI.

This server lets the extension send tasks/messages and receive
agent progress updates.

Protocol (extension -> backend):
- {"type": "ping"}
- {"type": "start_task", "task": "..."}
- {"type": "stop_task"}

Protocol (backend -> extension):
- {"type": "state_update", "state": {...}}
- {"type": "agent_message", "role": "assistant"|"system", "text": "..."}
- {"type": "task_started", "task": "..."}
- {"type": "task_completed", "success": bool, "result": "...", "steps": int}
- {"type": "task_failed", "error": "...", "steps": int}
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from aiohttp import web

from config.config import config
from src.core.execution_loop import ExecutionLoop
from src.utils.logger import log


@dataclass
class ServerState:
    is_running: bool = False
    current_task: Optional[str] = None
    websocket_connected: bool = False


class ExtensionBackendServer:
    def __init__(self):
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._ws: Optional[web.WebSocketResponse] = None
        self._task_handle: Optional[asyncio.Task] = None
        self.state = ServerState()

        self.loop = ExecutionLoop()
        # Inject a callback hook for streaming updates to the extension.
        self.loop.event_callback = self._on_agent_event

    async def _send(self, payload: Dict[str, Any]) -> None:
        if not self._ws or self._ws.closed:
            return
        await self._ws.send_str(json.dumps(payload, ensure_ascii=False))

    async def _broadcast_state(self) -> None:
        await self._send({
            "type": "state_update",
            "state": {
                "isRunning": self.state.is_running,
                "currentTask": self.state.current_task,
                "websocketConnected": self.state.websocket_connected,
            },
        })

    async def _on_agent_event(self, event: Dict[str, Any]) -> None:
        # event is expected to be JSON-serializable
        await self._send(event)

    async def _run_task(self, task: str) -> None:
        self.state.is_running = True
        self.state.current_task = task
        await self._send({"type": "task_started", "task": task})
        await self._broadcast_state()

        try:
            result = await self.loop.execute_task(task)
            await self._send({
                "type": "task_completed" if result.get("success") else "task_failed",
                "success": bool(result.get("success")),
                "result": result.get("result", ""),
                "error": None if result.get("success") else result.get("result", ""),
                "steps": int(result.get("steps", 0)),
            })
        except asyncio.CancelledError:
            await self._send({
                "type": "task_failed",
                "success": False,
                "error": "Task cancelled",
                "steps": int(getattr(self.loop, "current_step", 0) or 0),
            })
            raise
        except Exception as e:
            await self._send({
                "type": "task_failed",
                "success": False,
                "error": str(e),
                "steps": int(getattr(self.loop, "current_step", 0) or 0),
            })
        finally:
            self.state.is_running = False
            self.state.current_task = None
            await self._broadcast_state()

    async def _stop_task(self) -> None:
        log.info("Stop requested")
        if self._task_handle and not self._task_handle.done():
            self._task_handle.cancel()
            try:
                await self._task_handle
            except Exception:
                pass
        self._task_handle = None

    async def ws_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)

        # Single-client model (replace previous connection)
        if self._ws and not self._ws.closed:
            await self._ws.close(code=1000, message=b"Replaced by new client")

        self._ws = ws
        self.state.websocket_connected = True
        await self._broadcast_state()
        log.info("Extension WebSocket connected")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except Exception:
                        await self._send({"type": "error", "message": "Invalid JSON"})
                        continue

                    mtype = data.get("type")
                    if mtype == "ping":
                        await self._send({"type": "pong"})
                    elif mtype == "get_state":
                        await self._broadcast_state()
                    elif mtype == "start_task":
                        task = (data.get("task") or "").strip()
                        if not task:
                            await self._send({"type": "error", "message": "Empty task"})
                            continue
                        if self._task_handle and not self._task_handle.done():
                            await self._send({"type": "error", "message": "Agent is already running"})
                            continue
                        self._task_handle = asyncio.create_task(self._run_task(task))
                    elif mtype == "stop_task":
                        await self._stop_task()
                    else:
                        await self._send({"type": "error", "message": f"Unknown message type: {mtype}"})

                elif msg.type == web.WSMsgType.ERROR:
                    log.warning(f"WebSocket error: {ws.exception()}")
                    break

        finally:
            self.state.websocket_connected = False
            await self._broadcast_state()
            log.info("Extension WebSocket disconnected")

        return ws

    async def start(self, host: str = "127.0.0.1", port: Optional[int] = None) -> None:
        app = web.Application()
        app.router.add_get("/", lambda _: web.Response(text="OK"))
        app.router.add_get("/ws", self.ws_handler)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, host=host, port=port or config.WEBSOCKET_PORT)
        await self._site.start()

        log.success(f"Extension backend running: ws://{host}:{port or config.WEBSOCKET_PORT}/ws")

    async def stop(self) -> None:
        await self._stop_task()
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()


async def run_server_forever() -> None:
    server = ExtensionBackendServer()
    await server.start()
    # Keep running
    while True:
        await asyncio.sleep(3600)
