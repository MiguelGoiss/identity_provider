from typing import List, Tuple
from app.database.repository.app_window.app_window_repository import AppWindowRepository
from app.database.models.app_window import AppWindow
from app.schemas.app_window_schemas import AppWindowSyncItem


class AppWindowService:

    @staticmethod
    async def get_all() -> List[AppWindow]:
        return await AppWindowRepository.get_all()

    @staticmethod
    async def sync_windows(items: List[AppWindowSyncItem]) -> Tuple[int, int]:
        return await AppWindowRepository.sync_windows(items)
