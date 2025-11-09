import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.order import (
    create_order,
    get_order_by_id,
    get_orders_by_buyer
)
from app.schemas.order import OrderCreate


@pytest.mark.asyncio
async def test_create_order(db_session: AsyncSession, test_user, test_product):
    """Test creating a new order"""
    order_data = OrderCreate(
        product_id=test_product.id,
        quantity=2,
        message="Test order"
    )
    order = await create_order(db_session, order_data, test_user.id)
    
    assert order is not None
    assert order.id is not None
    assert order.product_id == test_product.id
    assert order.buyer_id == test_user.id
    assert order.quantity == 2
    assert order.total_price == test_product.price * 2


@pytest.mark.asyncio
async def test_get_order_by_id(db_session: AsyncSession, test_user, test_product):
    """Test getting order by ID"""
    order_data = OrderCreate(
        product_id=test_product.id,
        quantity=1
    )
    created_order = await create_order(db_session, order_data, test_user.id)
    
    order = await get_order_by_id(db_session, created_order.id)
    
    assert order is not None
    assert order.id == created_order.id
    assert order.product_id == test_product.id


@pytest.mark.asyncio
async def test_get_orders_by_buyer(db_session: AsyncSession, test_user, test_product):
    """Test getting orders by buyer"""
    # Create multiple orders
    order_data1 = OrderCreate(product_id=test_product.id, quantity=1)
    order_data2 = OrderCreate(product_id=test_product.id, quantity=2)
    
    await create_order(db_session, order_data1, test_user.id)
    await create_order(db_session, order_data2, test_user.id)
    
    orders = await get_orders_by_buyer(db_session, test_user.id)
    assert len(orders) >= 2


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(db_session: AsyncSession, test_user, test_product):
    """Test creating order with insufficient stock"""
    order_data = OrderCreate(
        product_id=test_product.id,
        quantity=9999  # More than available stock
    )
    order = await create_order(db_session, order_data, test_user.id)
    
    assert order is None  # Should fail due to insufficient stock

