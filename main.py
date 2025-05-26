from fastapi import FastAPI
import logging

from db.database import create_db_tables
from api.routers import tools_router, workflows_router
from core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic AI Backend",
    description="Backend for no-code agentic AI platform using CrewAI.",
    version="0.2.0"
)

@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables if they don't exist...")
    create_db_tables()
    logger.info("Database tables checked/created.")
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY environment variable is not set. CrewAI may not function.")
    if not settings.SERPER_API_KEY:
        logger.warning("SERPER_API_KEY environment variable is not set. SerperDevTool will not function.")


# Include routers
app.include_router(tools_router.router)
app.include_router(workflows_router.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to Agentic AI Backend"}


@app.get("/healthz", status_code=200)
async def healthz():
    return {"status": "ok"}