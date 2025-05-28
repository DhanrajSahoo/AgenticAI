from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import traceback
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

origins = [
    "*",         # todo: change after the UI url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    logger.info("FastAPI application starting up...")
    
    # Check critical settings first
    logger.info(f"Environment: {getattr(settings, 'env', 'not set')}")
    logger.info(f"Secret name: {getattr(settings, 'secret_cred_name', 'not set')}")
    
    try:
        logger.info("Creating database tables if they don't exist...")
        create_db_tables()
        logger.info("Database tables checked/created successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't raise - let app start without DB for debugging
        logger.warning("Continuing startup without database initialization...")
    
    # Check API keys with better logging
    try:
        if hasattr(settings, 'OPENAI_API_KEY'):
            if settings.OPENAI_API_KEY:
                logger.info("OPENAI_API_KEY is configured")
            else:
                logger.warning("OPENAI_API_KEY is not set")
        else:
            logger.warning("OPENAI_API_KEY setting not found")
            
        if hasattr(settings, 'SERPER_API_KEY'):
            if settings.SERPER_API_KEY:
                logger.info("SERPER_API_KEY is configured")
            else:
                logger.warning("SERPER_API_KEY is not set")
        else:
            logger.warning("SERPER_API_KEY setting not found")
            
    except Exception as e:
        logger.error(f"Error checking API keys: {e}")
    
    logger.info("Startup sequence completed.")

# Include routers
app.include_router(tools_router.router)
app.include_router(workflows_router.router)

@app.get("/", tags=["Root"])
async def read_root():
    try:
        return {"message": "Welcome to Agentic AI Backend"}
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        raise

@app.get("/healthz", status_code=200)
async def healthz():
    try:
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise
