import unittest
import sys
import os

# Ensure the app folder is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.schemas.user.user_schemas import UserContactResponse

class MockContactType:
    def __init__(self, slug: str, label: str):
        self.slug = slug
        self.label = label

class MockUserContact:
    def __init__(self, contact_type, value: str, description: str | None, is_public: bool, is_primary: bool):
        self.contact_type = contact_type
        self.value = value
        self.description = description
        self.is_public = is_public
        self.is_primary = is_primary

class TestUserSchemas(unittest.TestCase):
    
    def test_user_contact_response_with_model_object(self):
        # Create a mock ContactType object mimicking a Tortoise model relation
        contact_type_obj = MockContactType(slug="TELEMOVEL", label="Telemóvel")
        # Create a mock UserContact object
        user_contact_obj = MockUserContact(
            contact_type=contact_type_obj,
            value="+351912345678",
            description="Personal mobile",
            is_public=True,
            is_primary=True
        )
        
        # Test Pydantic validation (from_attributes)
        response = UserContactResponse.model_validate(user_contact_obj)
        self.assertEqual(response.contact_type, "TELEMOVEL")
        self.assertEqual(response.value, "+351912345678")
        self.assertEqual(response.description, "Personal mobile")
        self.assertTrue(response.is_public)
        self.assertTrue(response.is_primary)

    def test_user_contact_response_with_dict(self):
        # Test standard dict validation (direct input)
        data = {
            "contact_type": "DDI",
            "value": "+351291123456",
            "description": "Office direct",
            "is_public": False,
            "is_primary": False
        }
        response = UserContactResponse.model_validate(data)
        self.assertEqual(response.contact_type, "DDI")
        self.assertEqual(response.value, "+351291123456")
        self.assertEqual(response.description, "Office direct")
        self.assertFalse(response.is_public)
        self.assertFalse(response.is_primary)


if __name__ == "__main__":
    unittest.main()
