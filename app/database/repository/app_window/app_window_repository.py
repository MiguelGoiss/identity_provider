from typing import List, Optional, Tuple
from tortoise.transactions import in_transaction
from app.database.models.app_window import AppWindow
from app.schemas.app_window_schemas import AppWindowSyncItem


class AppWindowRepository:

    @staticmethod
    async def get_all() -> List[AppWindow]:
        """Return all app windows ordered by order field."""
        return await AppWindow.all().order_by("order").prefetch_related("parent")

    @staticmethod
    async def sync_windows(items: List[AppWindowSyncItem]) -> Tuple[int, int]:
        """
        Upsert app windows by slug.
        - Resolves parent_slug -> parent_id.
        - Returns (created_count, updated_count).
        """
        created = 0
        updated = 0

        async with in_transaction():
            # Build a slug->id map for parent resolution
            existing = await AppWindow.all()
            slug_to_id = {w.slug: w.id for w in existing}
            slug_to_obj = {w.slug: w for w in existing}

            for item in items:
                parent_id = None
                if item.parent_slug:
                    parent_id = slug_to_id.get(item.parent_slug)

                defaults = {
                    "name": item.name,
                    "icon": item.icon,
                    "parent_id": parent_id,
                    "order": item.order,
                }

                if item.slug in slug_to_obj:
                    # Update existing
                    obj = slug_to_obj[item.slug]
                    changed = False
                    for field, value in defaults.items():
                        if getattr(obj, field) != value:
                            setattr(obj, field, value)
                            changed = True
                    if changed:
                        await obj.save()
                        updated += 1
                else:
                    # Create new
                    obj = await AppWindow.create(slug=item.slug, **defaults)
                    slug_to_id[item.slug] = obj.id
                    slug_to_obj[item.slug] = obj
                    created += 1

        return created, updated
