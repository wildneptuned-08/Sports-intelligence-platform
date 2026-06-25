from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get_by_id(self, entity_id: int) -> T | None:
        return await self._session.get(self._model, entity_id)

    async def get_by_external_id(self, external_id: str) -> T | None:
        stmt = select(self._model).where(self._model.external_id == external_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> T:
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def update(self, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        if hasattr(instance, "updated_at"):
            instance.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return instance

    async def upsert(self, external_id: str, **kwargs) -> tuple[T, bool]:
        existing = await self.get_by_external_id(external_id)
        if existing:
            instance = await self.update(existing, **kwargs)
            return instance, False
        instance = await self.create(external_id=external_id, **kwargs)
        return instance, True

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[T]:
        stmt = select(self._model).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar_one()
