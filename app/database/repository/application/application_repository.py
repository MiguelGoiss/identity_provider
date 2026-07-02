from typing import List, Optional
from app.database.models.application import Application
from app.schemas.application_schemas import ApplicationCreate, ApplicationUpdate


class ApplicationRepository:

    @staticmethod
    async def create(data: ApplicationCreate) -> Application:
        return await Application.create(
            slug=data.slug,
            name=data.name,
        )

    @staticmethod
    async def get_all() -> List[Application]:
        return await Application.all().order_by("name")

    @staticmethod
    async def get_by_id(app_id: int) -> Optional[Application]:
        return await Application.get_or_none(id=app_id)

    @staticmethod
    async def update(app_id: int, data: ApplicationUpdate) -> Optional[Application]:
        obj = await Application.get_or_none(id=app_id)
        if not obj:
            return None
        update_dict = data.model_dump(exclude_unset=True)
        if update_dict:
            obj.update_from_dict(update_dict)
            await obj.save()
        return obj
