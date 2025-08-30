# main.py

from fastapi import FastAPI
from api.auth_routes import auth_router
from api.chain_routes import chain_router
from ws.ws_routes import ws_router
from utils.utils import create_logger
from utils.constants import MAIN_APP_LOG_FILENAME
from src.main import initialize_models # <--- IMPORT THE INITIALIZER

# Set up logging
log_file = MAIN_APP_LOG_FILENAME
logger = create_logger(log_file)

app = FastAPI(
    title="Odoo HR Bot API",
    description="API for interacting with the AI-powered HR assistant."
)

@app.on_event("startup")
async def startup_event():
    """
    This event handler runs the model initialization at startup.
    """
    initialize_models()

logger.info("Starting up the Odoo HR Bot application...")

# Include all the necessary routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chain_router, prefix="/api", tags=["RAG Chains"])
app.include_router(ws_router, tags=["WebSockets"])

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint handler.

    Returns:
        A welcome message dictionary.
    """
    return {"message": "Welcome to the Odoo HR Bot API!"}