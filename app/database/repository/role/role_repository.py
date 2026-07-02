from typing import List, Optional
from tortoise.transactions import in_transaction
from app.database.models.role import Role
from app.database.models.permission import Permission
from app.database.models.app_window import AppWindow
from app.database.models.user import User
from app.schemas.role_schemas import RoleCreate, RoleUpdate


class RoleRepository:

  # ------------------------------------------------------------------ #
  # Original helpers (kept for backward compat with auth_router.py)
  # ------------------------------------------------------------------ #

  @staticmethod
  async def add_permission_to_role(role_id: int, permission_id: int) -> Role | None:
    role = await Role.get_or_none(id=role_id)
    if not role:
      return None
    permission = await Permission.get_or_none(id=permission_id)
    if not permission:
      return None
    await role.permissions.add(permission)
    return role

  @staticmethod
  async def add_role_to_user(user_id: int, role_id: int) -> bool:
    user = await User.get_or_none(id=user_id)
    if not user:
      return False
    role = await Role.get_or_none(id=role_id)
    if not role:
      return False
    await user.roles.add(role)
    return True

  @staticmethod
  async def get_user_permissions(user_id: int) -> List[str]:
    user = await User.get_or_none(id=user_id).prefetch_related('roles__permissions')
    if not user:
      return []

    permissions = set()
    for role in user.roles:
      for permission in role.permissions:
        permissions.add(permission.slug)

    return list(permissions)

  @staticmethod
  async def get_user_permissions_grouped(user_id: int) -> dict[str, List[str]]:
    user = await User.get_or_none(id=user_id).prefetch_related('roles__permissions__app_window')
    if not user:
      return {}

    grouped = {}
    for role in user.roles:
      for permission in role.permissions:
        window_slug = "global"
        if permission.app_window:
          window_slug = permission.app_window.slug

        if window_slug not in grouped:
          grouped[window_slug] = set()
        grouped[window_slug].add(permission.slug)

    return {win: list(perms) for win, perms in grouped.items()}

  # ------------------------------------------------------------------ #
  # New CRUD
  # ------------------------------------------------------------------ #

  @staticmethod
  async def get_all_roles(company_id: Optional[int] = None) -> List[Role]:
    """List roles with optional company_id filter."""
    qs = Role.all()
    if company_id is not None:
      qs = qs.filter(company_id=company_id)
    return await qs.order_by("name")

  @staticmethod
  async def create_role(role_data: RoleCreate) -> Role:
    async with in_transaction():
      role = await Role.create(
        name=role_data.name,
        company_id=role_data.company_id
      )
      if role_data.permission_ids:
        permissions = await Permission.filter(id__in=role_data.permission_ids)
        await role.permissions.add(*permissions)
      if role_data.app_window_ids:
        windows = await AppWindow.filter(id__in=role_data.app_window_ids)
        await role.accessible_windows.add(*windows)
      return role

  @staticmethod
  async def get_role_detail(role_id: int) -> Optional[dict]:
    """
    Returns role base data + ALL permissions (with assigned flag)
    + ALL app_windows (with accessible flag).
    """
    role = await Role.get_or_none(id=role_id)
    if not role:
      return None

    # Fetch assigned sets
    assigned_permissions = await role.permissions.all()
    assigned_windows = await role.accessible_windows.all()
    assigned_perm_ids = {p.id for p in assigned_permissions}
    assigned_win_ids = {w.id for w in assigned_windows}

    # Fetch universe
    all_permissions = await Permission.all().order_by("slug")
    all_windows = await AppWindow.all().order_by("order")

    company_id = None
    try:
      company_id = role.company_id
    except Exception:
      pass

    return {
      "id": role.id,
      "name": role.name,
      "company_id": company_id,
      "permissions": [
        {
          "id": p.id,
          "slug": p.slug,
          "description": p.description,
          "app_window_id": p.app_window_id,
          "assigned": p.id in assigned_perm_ids,
        }
        for p in all_permissions
      ],
      "app_windows": [
        {
          "id": w.id,
          "name": w.name,
          "slug": w.slug,
          "icon": w.icon,
          "parent_id": w.parent_id,
          "order": w.order,
          "accessible": w.id in assigned_win_ids,
        }
        for w in all_windows
      ],
    }

  @staticmethod
  async def update_role(role_id: int, data: RoleUpdate) -> Optional[Role]:
    """
    Replace-update a role.
    - If name is provided, update it.
    - If permission_ids is provided, replace the full set.
    - If app_window_ids is provided, replace the full set.
    """
    role = await Role.get_or_none(id=role_id)
    if not role:
      return None

    async with in_transaction():
      if data.name is not None:
        role.name = data.name
        await role.save()

      if data.permission_ids is not None:
        await role.permissions.clear()
        if data.permission_ids:
          new_perms = await Permission.filter(id__in=data.permission_ids)
          await role.permissions.add(*new_perms)

      if data.app_window_ids is not None:
        await role.accessible_windows.clear()
        if data.app_window_ids:
          new_windows = await AppWindow.filter(id__in=data.app_window_ids)
          await role.accessible_windows.add(*new_windows)

    # Return prefetched for response
    await role.fetch_related("permissions")
    return role

  @staticmethod
  async def delete_role(role_id: int) -> bool:
    role = await Role.get_or_none(id=role_id)
    if not role:
      return False
    await role.delete()
    return True
