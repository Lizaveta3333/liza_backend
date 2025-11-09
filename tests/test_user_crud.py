import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.user import (
    create_user,
    get_user_by_id,
    get_user_by_email_or_phone,
    update_user_data,
    delete_user,
    get_all_users
)
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test creating a new user"""
    user_data = UserCreate(
        phone="+1111111111",
        password="password123",
        full_name="John Doe",
        rating=5.0
    )
    user = await create_user(db_session, user_data)
    
    assert user.id is not None
    assert user.phone == "+1111111111"
    assert user.full_name == "John Doe"
    assert user.rating == 5.0
    assert user.hashed_password != "password123"  # Should be hashed


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession, test_user):
    """Test getting user by ID"""
    user = await get_user_by_id(db_session, test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.phone == test_user.phone


@pytest.mark.asyncio
async def test_get_user_by_phone(db_session: AsyncSession, test_user):
    """Test getting user by phone"""
    user = await get_user_by_email_or_phone(db_session, phone=test_user.phone)
    
    assert user is not None
    assert user.phone == test_user.phone


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession, test_user):
    """Test updating user data"""
    update_data = UserUpdate(
        full_name="Updated Name",
        about="Updated about"
    )
    updated_user = await update_user_data(db_session, test_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.about == "Updated about"
    assert updated_user.phone == test_user.phone  # Unchanged


@pytest.mark.asyncio
async def test_delete_user(db_session: AsyncSession, test_user):
    """Test deleting a user"""
    deleted_user = await delete_user(test_user.id, db_session)
    
    assert deleted_user is not None
    assert deleted_user.id == test_user.id
    
    # Verify user is deleted
    user = await get_user_by_id(db_session, test_user.id)
    assert user is None


@pytest.mark.asyncio
async def test_get_all_users(db_session: AsyncSession, test_user):
    """Test getting all users"""
    # Create another user
    user_data = UserCreate(
        phone="+2222222222",
        password="password123",
        full_name="Jane Doe",
        rating=4.5
    )
    await create_user(db_session, user_data)
    
    users = await get_all_users(db_session)
    assert len(users) >= 2

