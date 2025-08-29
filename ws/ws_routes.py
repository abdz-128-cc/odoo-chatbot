# odoo_bot/ws/ws_routes.py

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.main import chat_once  # <-- IMPORT the new RAG core
from ws.helper import get_current_user_from_token
import logging

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    username = user.get("username", "unknown_user")
    role = user.get("role", "employee")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("query")

            if not query:
                continue

            # --- RAG Core Integration ---
            # 1. Acknowledge receipt and show a "thinking" state
            await websocket.send_text(json.dumps({"type": "status", "message": "Thinking..."}))

            # 2. Call the synchronous chat_once function
            try:
                route, answer = chat_once(question=query, role=role, user_id=username)

                # 3. Send the final answer
                await websocket.send_text(json.dumps({
                    "type": "final_answer",
                    "answer": answer,
                    "route": route
                }))
            except Exception as e:
                logger.error(f"Error in chat_once for websocket user '{username}': {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Sorry, I encountered an error. Please try again."
                }))
            # --- End Integration ---

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {username}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the websocket: {e}")