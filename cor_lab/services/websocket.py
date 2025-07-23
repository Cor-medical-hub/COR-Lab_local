from fastapi import WebSocket
from loguru import logger

active_connections: dict[str, WebSocket] = {}


async def send_websocket_message(session_token: str, message: dict):
    """Отправляет сообщение через WebSocket конкретному клиенту."""
    if session_token in active_connections:
        await active_connections[session_token].send_json(message)


async def close_websocket_connection(session_token: str):
    """Закрывает WebSocket-соединение и удаляет его из активных."""
    if session_token in active_connections:
        await active_connections[session_token].close()
        del active_connections[session_token]
        logger.debug(
            f"WebSocket соединение для {session_token} закрыто из-за таймаута."
        )
