from fastapi import APIRouter, Depends, status

from app.schemas.app_window_schemas import AppWindowResponse, AppWindowSyncRequest, AppWindowSyncResult
from app.services.app_window.app_window_service import AppWindowService
from app.core.permissions import PermissionChecker
from app.database.models.user import User

router = APIRouter(prefix="/app-windows", tags=["App Windows"])


@router.get("", response_model=list[AppWindowResponse])
async def list_app_windows(
    current_user: User = Depends(PermissionChecker("role:read")),
):
    """
    List all registered AppWindows / UI areas.
    Used by the role editor to display the accessible windows multiselect.
    """
    windows = await AppWindowService.get_all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "slug": w.slug,
            "icon": w.icon,
            "parent_id": w.parent_id,
            "order": w.order,
        }
        for w in windows
    ]


@router.post(
    "/sync",
    response_model=AppWindowSyncResult,
    status_code=status.HTTP_200_OK,
)
async def sync_app_windows(
    payload: AppWindowSyncRequest,
    current_user: User = Depends(PermissionChecker("appwindow:sync")),
):
    """
    Upsert AppWindows by slug.

    Send a list of window/URI definitions (from gateway OpenAPI scan or
    frontend static list). The server creates missing entries and updates
    existing ones. Parent relationships are resolved via `parent_slug`.

    Returns counts of created and updated records.
    """
    created, updated = await AppWindowService.sync_windows(payload.windows)
    return AppWindowSyncResult(created_count=created, updated_count=updated)
