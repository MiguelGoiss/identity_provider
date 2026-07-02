import unittest
import sys
import os

# Ensure the app folder is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.utils.query_parser import QueryParser, UnsupportedFilterError

class TestQueryParser(unittest.TestCase):
    
    def test_parse_filters_empty(self):
        self.assertEqual(QueryParser.parse_filters([]), {})
        self.assertEqual(QueryParser.parse_filters(None), {})

    def test_parse_filters_invalid_format(self):
        # Missing operator or value, or incorrect splits
        filters = ["username", "username:eq", "username::admin", "username:eq:"]
        
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(["username"])
            
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(["username:eq"])
            
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(["username::admin"])
            
        # username:eq: should be valid as eq with empty string
        self.assertEqual(QueryParser.parse_filters(["username:eq:"]), {"identities__identifier_idx": ""})

    def test_parse_filters_unallowed_field(self):
        # Fields not in FIELDS should raise UnsupportedFilterError
        filters = ["password:eq:secret"]
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(filters)

        filters = ["some_random_field:eq:123"]
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(filters)

    def test_parse_filters_invalid_operator(self):
        # Operators not in allowed_ops should raise UnsupportedFilterError
        filters = ["username:invalid_op:admin"]
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(filters)
            
        # Valid operator but not allowed for this field
        filters = ["email:like:admin"]
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_filters(filters)

    def test_parse_filters_valid_basic(self):
        filters = [
            "id:eq:123",
            "first_name:ilike:john",
            "org_unit_is_active:eq:true"
        ]
        result = QueryParser.parse_filters(filters)
        self.assertEqual(result, {
            "id": "123",
            "profile__first_name__icontains": "john",
            "is_active": True
        })

    def test_parse_filters_boolean_conversions(self):
        self.assertEqual(QueryParser.parse_filters(["org_unit_is_active:eq:true"]), {"is_active": True})
        self.assertEqual(QueryParser.parse_filters(["org_unit_is_active:eq:TRUE"]), {"is_active": True})
        self.assertEqual(QueryParser.parse_filters(["org_unit_is_active:eq:false"]), {"is_active": False})
        self.assertEqual(QueryParser.parse_filters(["org_unit_is_active:eq:FALSE"]), {"is_active": False})

    def test_parse_filters_in_operators(self):
        # 'in' operator splits value by comma
        self.assertEqual(QueryParser.parse_filters(["org_unit_name:in:dept1,dept2"]), {"name__in": ["dept1", "dept2"]})
        self.assertEqual(QueryParser.parse_filters(["company_id:not_in:4,5"]), {"companies__company__id__not_in": ["4", "5"]})

    def test_parse_filters_isnull_operator(self):
        self.assertEqual(QueryParser.parse_filters(["created_at:isnull:true"]), {"created_at__isnull": True})
        self.assertEqual(QueryParser.parse_filters(["created_at:isnull:TRUE"]), {"created_at__isnull": True})
        self.assertEqual(QueryParser.parse_filters(["created_at:isnull:false"]), {"created_at__isnull": False})
        self.assertEqual(QueryParser.parse_filters(["created_at:isnull:abc"]), {"created_at__isnull": False}) # any non-true string is False

    def test_parse_filters_company_mappings(self):
        # Verify that company_id and company_name map to companies__company__id and companies__company__name
        self.assertEqual(QueryParser.parse_filters(["company_id:eq:10"]), {"companies__company__id": "10"})
        self.assertEqual(QueryParser.parse_filters(["company_name:ilike:savoy"]), {"companies__company__name__icontains": "savoy"})

    def test_parse_order_empty(self):
        self.assertEqual(QueryParser.parse_order(None), [])
        self.assertEqual(QueryParser.parse_order(""), [])

    def test_parse_order_single_and_multi(self):
        # Single field ascending
        self.assertEqual(QueryParser.parse_order("first_name"), ["profile__first_name"])
        # Single field descending
        self.assertEqual(QueryParser.parse_order("-first_name"), ["-profile__first_name"])
        # Multi fields
        self.assertEqual(
            QueryParser.parse_order("-created_at,company_name"),
            ["-created_at", "companies__company__name"]
        )
        # Verify that company fields map properly in order too
        self.assertEqual(QueryParser.parse_order("-local_name"), ["-local__name"])

    def test_parse_order_invalid_fields(self):
        # Invalid fields should raise UnsupportedFilterError
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_order("password")
        
        with self.assertRaises(UnsupportedFilterError):
            QueryParser.parse_order("-email") # not orderable


if __name__ == "__main__":
    unittest.main()
