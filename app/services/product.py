from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: AsyncSession, tenant_id: int) -> None:
        self.repo = ProductRepository(session, tenant_id)

    async def create(self, data: ProductCreate) -> Product:
        if data.sku:
            existing = await self.repo.get_by_sku(data.sku)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{data.sku}' already exists",
                )
        return await self.repo.create(**data.model_dump())

    async def get_or_404(self, product_id: int) -> Product:
        product = await self.repo.get(product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        return product

    async def list_active(self) -> list[Product]:
        return await self.repo.get_active()

    async def list_all(self) -> list[Product]:
        return list(await self.repo.get_all())

    async def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = await self.get_or_404(product_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        return product

    async def delete(self, product_id: int) -> None:
        product = await self.get_or_404(product_id)
        await self.repo.delete(product)
