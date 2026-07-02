import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Ensure the app folder is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.permission_schemas import PermissionCreate, PermissionUpdate, PermissionResponse
from app.database.repository.permission.permission_repository import PermissionRepository
from app.database.repository.role.role_repository import RoleRepository

class TestPermissionAppWindow(unittest.IsolatedAsyncioTestCase):

    @patch("app.database.repository.permission.permission_repository.Permission.get_or_create", new_callable=AsyncMock)
    async def test_create_permission_with_app_window(self, mock_get_or_create):
        # Arrange
        mock_permission = MagicMock()
        mock_permission.slug = "test:slug"
        mock_permission.description = "Test Description"
        mock_permission.app_window_id = 45
        mock_permission.save = AsyncMock()

        mock_get_or_create.return_value = (mock_permission, True)

        permission_data = PermissionCreate(
            slug="test:slug",
            description="Test Description",
            app_window_id=45
        )

        # Act
        result = await PermissionRepository.create_permission(permission_data)

        # Assert
        mock_get_or_create.assert_called_once_with(
            slug="test:slug",
            defaults={
                "description": "Test Description",
                "app_window_id": 45
            }
        )
        self.assertEqual(result.slug, "test:slug")
        self.assertEqual(result.description, "Test Description")
        self.assertEqual(result.app_window_id, 45)

    @patch("app.database.repository.permission.permission_repository.Permission.get_or_none", new_callable=AsyncMock)
    async def test_update_permission_with_app_window(self, mock_get_or_none):
        # Arrange
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.slug = "test:slug"
        mock_permission.description = "Old Description"
        mock_permission.app_window_id = 10
        mock_permission.save = AsyncMock()

        mock_get_or_none.return_value = mock_permission

        update_data = PermissionUpdate(
            description="New Description",
            app_window_id=20
        )

        # Act
        result = await PermissionRepository.update_permission(1, update_data)

        # Assert
        self.assertEqual(result.description, "New Description")
        self.assertEqual(result.app_window_id, 20)
        mock_permission.save.assert_called_once()


    @patch("app.database.repository.role.role_repository.User.get_or_none")
    async def test_get_user_permissions_grouped(self, mock_get_user):
        # Arrange
        mock_user = MagicMock()
        mock_user.id = 123
        
        # Mock window and permission
        mock_window = MagicMock()
        mock_window.slug = "users-window"
        
        mock_permission1 = MagicMock()
        mock_permission1.slug = "user:create"
        mock_permission1.app_window = mock_window
        
        mock_permission2 = MagicMock()
        mock_permission2.slug = "global:access"
        mock_permission2.app_window = None  # global/no window
        
        mock_role = MagicMock()
        mock_role.permissions = [mock_permission1, mock_permission2]
        
        mock_user.roles = [mock_role]
        
        mock_qs = MagicMock()
        mock_get_user.return_value = mock_qs
        mock_qs.prefetch_related = AsyncMock(return_value=mock_user)
        
        # Act
        result = await RoleRepository.get_user_permissions_grouped(123)
        
        # Assert
        self.assertIn("users-window", result)
        self.assertIn("global", result)
        self.assertIn("user:create", result["users-window"])
        self.assertIn("global:access", result["global"])


if __name__ == "__main__":
    unittest.main()
