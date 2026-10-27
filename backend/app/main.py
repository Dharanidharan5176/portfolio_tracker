import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.errors import AppError, app_error_handler, generic_exception_handler
from backend.app.db.base import Base
from backend.app.db.session import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist if not using alembic directly, and verify data dirs
    settings.data_path
    Base.metadata.create_all(bind=engine)
    logger.info("Local Portfolio Tracker API started cleanly on %s:%s", settings.APP_HOST, settings.APP_PORT)
    yield
    logger.info("Local Portfolio Tracker API shutting down.")

app = FastAPI(
    title="Local Portfolio Tracker API",
    version="1.0.0",
    description="Local-first personal portfolio tracker and analytics backend",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS restricted to local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}",
        f"http://localhost:{settings.FRONTEND_PORT}",
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response

# Error handling
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "service": "portfolio-tracker-api",
        "environment": settings.APP_ENV,
        "local_only": True
    }

# Include API v1 router when ready
from backend.app.api.v1.router import api_router
app.include_router(api_router, prefix="/api/v1")
