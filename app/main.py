from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api import router
from app.core.security import refresh_access_token_middleware
from app.services.kafka_service import get_producer, start_consumer, close_producer, close_consumer


app = FastAPI(
    title="Liza Backend API",
    description="API для магазина продуктов",
    version="1.0.0",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
    }
)

@app.on_event("startup")
async def on_startup():
    await create_tables()
    # Initialize Kafka producer and consumer
    get_producer()
    start_consumer()


@app.on_event("shutdown")
async def on_shutdown():
    # Close Kafka connections
    close_producer()
    close_consumer()


origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://192.168.1.30:3000",
    "http://10.223.187.14:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",  # Swagger UI
    "https://osteitic-ossie-noncomprehensiblely.ngrok-free.dev",
    "https://liza-frontend-app.onrender.com",  # Deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions, especially 400 errors with nice formatting"""
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Bad Request",
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Liza Backend API"}


app.middleware("http")(refresh_access_token_middleware)

app.include_router(router.router) 

# В проде через Alembic
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

