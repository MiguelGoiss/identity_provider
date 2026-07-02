import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import sys
import os

# Ensure the app folder is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app

class TestOTPAuthentication(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.routers.auth.auth_router.User.filter")
    @patch("app.routers.auth.auth_router.User.get", new_callable=AsyncMock)
    @patch("app.routers.auth.auth_router.UserEmail.get_or_none")
    @patch("app.routers.auth.auth_router.UserEmail.filter")
    @patch("app.routers.auth.auth_router.send_otp_email", new_callable=AsyncMock)
    @patch("app.routers.auth.auth_router.get_password_hash")
    async def test_validate_identifier_collaborator_success(self, mock_hash, mock_send_email, mock_filter, mock_get_email, mock_user_get, mock_user_filter):
        # Setup mock user and email
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_agent = False
        mock_user.recovery_secret = None
        mock_user.recovery_secret_expires_at = None
        mock_user.recovery_attempts = 0
        mock_user.deactivated_at = None
        mock_user.save = AsyncMock()

        mock_email_obj = MagicMock()
        mock_email_obj.user = mock_user
        mock_email_obj.email = "collaborator@example.com"

        # Mock UserEmail.get_or_none chain
        mock_qs = MagicMock()
        mock_get_email.return_value = mock_qs
        mock_qs.prefetch_related = AsyncMock(return_value=mock_email_obj)

        # Mock User.get
        mock_user_get.return_value = mock_user

        # Mock User.filter().update()
        mock_user_filter_qs = MagicMock()
        mock_user_filter.return_value = mock_user_filter_qs
        mock_user_filter_qs.update = AsyncMock()

        mock_hash.return_value = "hashed_otp_pin"
        mock_send_email.return_value = True

        # Call endpoint via test client
        response = self.client.post("/auth/.validate-identifier", json={"username": "collaborator@example.com"})

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_agent"])
        self.assertTrue(data["is_user"])
        self.assertTrue(data["is_collaborator"])
        
        # Verify direct DB update and email send
        mock_user_filter.assert_called_once_with(id=mock_user.id)
        mock_user_filter_qs.update.assert_called_once()
        mock_send_email.assert_called_once()

    @patch("app.routers.auth.auth_router.User.get", new_callable=AsyncMock)
    @patch("app.routers.auth.auth_router.UserEmail.get_or_none")
    @patch("app.routers.auth.auth_router.UserEmail.filter")
    async def test_validate_identifier_agent_success(self, mock_filter, mock_get_email, mock_user_get):
        # Setup mock user and email
        mock_user = MagicMock()
        mock_user.is_agent = True
        mock_user.deactivated_at = None

        mock_email_obj = MagicMock()
        mock_email_obj.user = mock_user
        mock_email_obj.email = "agent@example.com"

        # Mock UserEmail.get_or_none chain
        mock_qs = MagicMock()
        mock_get_email.return_value = mock_qs
        mock_qs.prefetch_related = AsyncMock(return_value=mock_email_obj)

        # Mock User.get
        mock_user_get.return_value = mock_user

        # Call endpoint
        response = self.client.post("/auth/.validate-identifier", json={"username": "agent@example.com"})

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_agent"])
        self.assertTrue(data["is_user"])
        self.assertFalse(data["is_collaborator"])

    @patch("app.routers.auth.auth_router.User.get_or_none")
    @patch("app.routers.auth.auth_router.UserEmail.get_or_none")
    @patch("app.routers.auth.auth_router.UserEmail.filter")
    async def test_validate_identifier_not_found(self, mock_filter, mock_get_email, mock_user_get):
        # Mock get_or_none returning a chain that ends in None
        mock_qs = MagicMock()
        mock_get_email.return_value = mock_qs
        mock_qs.prefetch_related = AsyncMock(return_value=None)

        # Mock filter returning a chain that ends in None
        mock_filter_qs = MagicMock()
        mock_filter.return_value = mock_filter_qs
        mock_first_qs = MagicMock()
        mock_filter_qs.first.return_value = mock_first_qs
        mock_first_qs.prefetch_related = AsyncMock(return_value=None)

        # Mock User.get_or_none returning a chain that ends in None
        mock_user_qs = MagicMock()
        mock_user_get.return_value = mock_user_qs
        mock_user_qs.prefetch_related = AsyncMock(return_value=None)

        # Call endpoint
        response = self.client.post("/auth/.validate-identifier", json={"username": "unknown@example.com"})

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_agent"])
        self.assertTrue(data["is_user"])
        self.assertTrue(data["is_collaborator"])

    @patch("app.routers.auth.auth_router.User.filter")
    @patch("app.routers.auth.auth_router.User.get", new_callable=AsyncMock)
    @patch("app.routers.auth.auth_router.UserEmail.get_or_none")
    @patch("app.routers.auth.auth_router.verify_password")
    @patch("app.routers.auth.auth_router.RoleRepository.get_user_permissions", new_callable=AsyncMock)
    async def test_login_collaborator_incorrect_otp(self, mock_perms, mock_verify, mock_get_email, mock_user_get, mock_user_filter):
        # Setup mock user and email
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.is_agent = False
        mock_user.hashed_password = "hashed_collaborator_password"
        mock_user.recovery_secret = "hashed_otp_pin"
        mock_user.recovery_secret_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        mock_user.recovery_attempts = 0
        mock_user.deactivated_at = None
        mock_user.save = AsyncMock()

        mock_email_obj = MagicMock()
        mock_email_obj.user = mock_user
        mock_email_obj.email = "collaborator@example.com"

        mock_qs = MagicMock()
        mock_get_email.return_value = mock_qs
        mock_qs.prefetch_related = AsyncMock(return_value=mock_email_obj)

        # Mock User.get
        mock_user_get.return_value = mock_user

        # Mock User.filter().update()
        mock_user_filter_qs = MagicMock()
        mock_user_filter.return_value = mock_user_filter_qs
        mock_user_filter_qs.update = AsyncMock()

        # mock_verify(entered_pw, correct_pw)
        # First verification (against hashed_password) returns False
        # Second verification (against recovery_secret) returns False
        mock_verify.side_effect = [False, False]

        # Call endpoint (FastAPI OAuth2 form uses username and password fields)
        response = self.client.post("/auth/login", data={"username": "collaborator@example.com", "password": "wrong_otp_pin"})

        # Assertions
        self.assertEqual(response.status_code, 419)
        
        # Verify attempts are incremented and saved
        self.assertEqual(mock_user.recovery_attempts, 1)
        mock_user_filter.assert_called_once_with(id=mock_user.id)
        mock_user_filter_qs.update.assert_called_once_with(recovery_attempts=1)

if __name__ == "__main__":
    unittest.main()
