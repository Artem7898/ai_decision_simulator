from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import (
    DecisionSimulatorException,
    custom_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.db.session import init_db
from app.api.endpoints import router as api_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting AI Decision Simulator...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down AI Decision Simulator...")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
    AI Decision Simulator - Model decisions for:
    - Relocation (e.g., Move to Berlin vs Amsterdam)
    - Purchases (e.g., Buy car A vs car B)
    - Jobs (e.g., Job offer A vs B)
    - Investments (e.g., Stocks vs Bonds)

    Features:
    - LLM-powered query structuring
    - External data integration (cost of living, taxes)
    - Monte Carlo simulations
    - AI-generated reports with recommendations
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(DecisionSimulatorException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX, tags=["Decision Simulator"])

# Шаблоны
templates = Jinja2Templates(directory="templates")

# Статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Корневой эндпоинт: отдаёт HTML для браузера, JSON для API-клиентов."""
    accept = request.headers.get("accept", "")

    if "text/html" in accept:
        return templates.TemplateResponse("index.html", {"request": request})

    return JSONResponse(content={
        "message": "AI Decision Simulator API",
        "name": "AI Decision Simulator API",
        "version": "1.0.0",
        "description": "API for intelligent decision simulation using Monte Carlo and LLM"
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}