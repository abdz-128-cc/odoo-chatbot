import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.main import chat_once, get_prompts_config  # <-- IMPORT the getter function
from ws.helper import get_current_user_from_token
import logging

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid user")
            return
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    await websocket.accept()
    username = user.get("username", "unknown_user")
    role = user.get("role", "employee")

    try:
        # Use the getter function to access the config at runtime
        prompts = get_prompts_config()
        welcome_message = prompts.get("welcome_message")
        if welcome_message:
            await websocket.send_text(json.dumps({
                "type": "final_answer",
                "answer": welcome_message.strip(),
                "route": "system_welcome"
            }))
    except Exception as e:
        logger.error(f"Failed to send welcome message to {username}: {e}")
    # ----------------------------------------------------

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            query = message_data.get("query")

            if not query:
                continue

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

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {username}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in the websocket for {username}: {e}")