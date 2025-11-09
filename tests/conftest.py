import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    from app.crud.user import create_user
    from app.schemas.user import UserCreate
    
    user_data = UserCreate(
        phone="+1234567890",
        password="testpass123",
        full_name="Test User",
        rating=5.0
    )
    user = await create_user(db_session, user_data)
    return user


@pytest.fixture(scope="function")
async def test_product(db_session: AsyncSession, test_user):
    """Create a test product"""
    from app.crud.product import create_product
    from app.schemas.product import ProductCreate
    
    product_data = ProductCreate(
        title="Test Product",
        description="Test Description",
        price=99.99,
        category="Test Category",
        stock=10
    )
    product = await create_product(db_session, product_data, test_user.id)
    return product

