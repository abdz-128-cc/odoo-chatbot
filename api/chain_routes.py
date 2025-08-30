# odoo_bot/api/chain_routes.py

from fastapi import APIRouter, Depends, HTTPException
from authentication.auth import get_current_active_user
from schemas.query import Query
from schemas.user import User
from src.main import chat_once  # <-- IMPORT the new RAG core function
from utils.utils import create_logger
from utils.constants import MAIN_APP_LOG_FILENAME
import traceback

# Set up logger
log_file = MAIN_APP_LOG_FILENAME
logger = create_logger(log_file)

chain_router = APIRouter()


@chain_router.post("/ask")
async def ask_question(query: Query, current_user: User = Depends(get_current_active_user)):
    """
    Processes a user's question through the RAG pipeline and returns the answer.

    Args:
        query: The query containing the user's question.
        current_user: The currently authenticated user (default obtained via dependency).

    Returns:
        A dictionary with the generated answer and the route taken.

    Raises:
        HTTPException: If an error occurs during query processing.
    """
    username = current_user.get("username", "unknown_user")
    role = current_user.get("role", "employee")

    logger.info(f"User '{username}' (role: {role}) asked: {query.question}")

    try:
        route, answer = chat_once(
            question=query.question,
            role=role,
            user_id=username
        )

        logger.info(f"Routed to '{route}'. Answer generated for '{username}'.")

        return {"answer": answer, "route": route}

    except Exception as e:
        logger.error(f"Error processing query for user '{username}': {e}")
        tb = traceback.format_exc()
        logger.error(tb)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")