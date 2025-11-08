from fastapi import FastAPI
from app.api import router
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(refresh_access_token_middleware)

app.include_router(router.router) 

# В проде через Alembic
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

