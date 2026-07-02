from typing import Optional
from app.database.repository.application.application_repository import ApplicationRepository
from app.schemas.application_schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse


class ApplicationService:

    @staticmethod
    async def create(data: ApplicationCreate) -> ApplicationResponse:
        obj = await ApplicationRepository.create(data)
        return ApplicationResponse.model_validate(obj)

    @staticmethod
    async def get_all() -> list[ApplicationResponse]:
        items = await ApplicationRepository.get_all()
        return [ApplicationResponse.model_validate(i) for i in items]

    @staticmethod
    async def update(app_id: int, data: ApplicationUpdate) -> Optional[ApplicationResponse]:
        obj = await ApplicationRepository.update(app_id, data)
        if not obj:
            return None
        return ApplicationResponse.model_validate(obj)
