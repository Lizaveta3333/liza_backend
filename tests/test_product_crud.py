import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.product import (
    create_product,
    get_product_by_id,
    update_product,
    delete_product,
    get_products_by_seller,
    get_all_products
)
from app.schemas.product import ProductCreate, ProductUpdate, ProductStatus


@pytest.mark.asyncio
async def test_create_product(db_session: AsyncSession, test_user):
    """Test creating a new product"""
    product_data = ProductCreate(
        title="Test Laptop",
        description="A test laptop",
        price=999.99,
        category="Electronics",
        stock=5
    )
    product = await create_product(db_session, product_data, test_user.id)
    
    assert product.id is not None
    assert product.title == "Test Laptop"
    assert product.price == 999.99
    assert product.seller_id == test_user.id
    assert product.status == ProductStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_get_product_by_id(db_session: AsyncSession, test_product):
    """Test getting product by ID"""
    product = await get_product_by_id(db_session, test_product.id)
    
    assert product is not None
    assert product.id == test_product.id
    assert product.title == test_product.title


@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession, test_product):
    """Test updating product data"""
    update_data = ProductUpdate(
        title="Updated Title",
        price=799.99,
        stock=3
    )
    updated_product = await update_product(db_session, test_product.id, update_data)
    
    assert updated_product is not None
    assert updated_product.title == "Updated Title"
    assert updated_product.price == 799.99
    assert updated_product.stock == 3
    assert updated_product.description == test_product.description  # Unchanged


@pytest.mark.asyncio
async def test_delete_product(db_session: AsyncSession, test_product):
    """Test deleting a product"""
    result = await delete_product(db_session, test_product.id)
    
    assert result is True
    
    # Verify product is deleted
    product = await get_product_by_id(db_session, test_product.id)
    assert product is None


@pytest.mark.asyncio
async def test_get_products_by_seller(db_session: AsyncSession, test_user, test_product):
    """Test getting products by seller"""
    # Create another product for the same seller
    product_data = ProductCreate(
        title="Another Product",
        description="Another description",
        price=199.99,
        category="Electronics",
        stock=2
    )
    await create_product(db_session, product_data, test_user.id)
    
    products = await get_products_by_seller(db_session, test_user.id)
    assert len(products) >= 2


@pytest.mark.asyncio
async def test_get_all_products(db_session: AsyncSession, test_product):
    """Test getting all products"""
    products = await get_all_products(db_session)
    assert len(products) >= 1
    assert any(p.id == test_product.id for p in products)

