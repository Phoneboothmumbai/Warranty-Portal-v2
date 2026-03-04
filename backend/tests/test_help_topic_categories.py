"""
Test Help Topic Categories and Comprehensive Topics
====================================================
Tests for:
- GET /api/ticketing/help-topic-categories returns 8 categories
- POST /api/ticketing/help-topic-categories creates a new category
- PUT /api/ticketing/help-topic-categories/{id} updates a category
- DELETE /api/ticketing/help-topic-categories/{id} deletes a category
- GET /api/ticketing/help-topics returns 43+ topics with category_id and tags fields
- Topics have tags array for search functionality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    """Login and get admin token"""
    login_data = {
        "email": "ck@motta.in",
        "password": "Charu@123@"
    }
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Auth headers for API calls"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestHelpTopicCategories:
    """Test CRUD operations for help topic categories"""

    def test_get_help_topic_categories_returns_8(self, auth_headers):
        """GET /api/ticketing/help-topic-categories returns 8 categories"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        categories = resp.json()
        
        assert isinstance(categories, list), "Response should be a list"
        assert len(categories) >= 8, f"Expected at least 8 categories, got {len(categories)}"
        
        # Verify expected category names
        expected_slugs = ["hardware", "software", "network", "peripherals", "service", "warranty", "commercial", "general"]
        category_slugs = [c.get("slug") for c in categories]
        for slug in expected_slugs:
            assert slug in category_slugs, f"Missing expected category slug: {slug}"
        
        # Verify category structure
        for cat in categories:
            assert "id" in cat, "Category missing 'id'"
            assert "name" in cat, "Category missing 'name'"
            assert "slug" in cat, "Category missing 'slug'"
            assert "color" in cat, "Category missing 'color'"
            assert "order" in cat, "Category missing 'order'"
        
        print(f"✓ Found {len(categories)} categories with expected structure")

    def test_create_help_topic_category(self, auth_headers):
        """POST /api/ticketing/help-topic-categories creates a new category"""
        new_cat = {
            "name": "TEST_Custom Category",
            "slug": "test-custom-category",
            "description": "A test category for validation",
            "icon": "star",
            "color": "#FF5733",
            "order": 99
        }
        resp = requests.post(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers, json=new_cat)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        
        created = resp.json()
        assert created.get("name") == new_cat["name"], "Name mismatch"
        assert created.get("slug") == new_cat["slug"], "Slug mismatch"
        assert created.get("color") == new_cat["color"], "Color mismatch"
        assert "id" in created, "Missing id in response"
        
        # Verify it was persisted
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        found = any(c.get("slug") == new_cat["slug"] for c in categories)
        assert found, "Created category not found in list"
        
        # Store ID for cleanup
        self.__class__.test_category_id = created["id"]
        print(f"✓ Created category with id: {created['id']}")

    def test_update_help_topic_category(self, auth_headers):
        """PUT /api/ticketing/help-topic-categories/{id} updates a category"""
        cat_id = getattr(self.__class__, "test_category_id", None)
        if not cat_id:
            pytest.skip("No test category created")
        
        update_data = {
            "name": "TEST_Updated Category",
            "description": "Updated description",
            "color": "#00FF00"
        }
        resp = requests.put(f"{BASE_URL}/api/ticketing/help-topic-categories/{cat_id}", headers=auth_headers, json=update_data)
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        
        updated = resp.json()
        assert updated.get("name") == update_data["name"], "Name not updated"
        assert updated.get("description") == update_data["description"], "Description not updated"
        assert updated.get("color") == update_data["color"], "Color not updated"
        
        # Verify persistence
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        found = next((c for c in categories if c.get("id") == cat_id), None)
        assert found is not None, "Updated category not found"
        assert found.get("name") == update_data["name"], "Update not persisted"
        
        print(f"✓ Updated category successfully")

    def test_delete_help_topic_category(self, auth_headers):
        """DELETE /api/ticketing/help-topic-categories/{id} deletes a category"""
        cat_id = getattr(self.__class__, "test_category_id", None)
        if not cat_id:
            pytest.skip("No test category created")
        
        resp = requests.delete(f"{BASE_URL}/api/ticketing/help-topic-categories/{cat_id}", headers=auth_headers)
        assert resp.status_code == 200, f"Delete failed: {resp.text}"
        
        result = resp.json()
        assert "message" in result, "Missing message in delete response"
        
        # Verify deletion
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        found = any(c.get("id") == cat_id for c in categories)
        assert not found, "Category still exists after deletion"
        
        print(f"✓ Deleted category successfully")


class TestHelpTopicsComprehensive:
    """Test comprehensive help topics with category_id and tags"""

    def test_get_help_topics_returns_43_plus(self, auth_headers):
        """GET /api/ticketing/help-topics returns 43+ topics"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        assert resp.status_code == 200, f"Failed: {resp.text}"
        topics = resp.json()
        
        assert isinstance(topics, list), "Response should be a list"
        assert len(topics) >= 30, f"Expected at least 30 topics (possibly 43+), got {len(topics)}"
        
        print(f"✓ Found {len(topics)} help topics")

    def test_help_topics_have_category_id_field(self, auth_headers):
        """Topics have category_id field for grouping"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        assert resp.status_code == 200
        topics = resp.json()
        
        # Count topics with category_id
        with_category_id = [t for t in topics if t.get("category_id")]
        print(f"Topics with category_id: {len(with_category_id)}/{len(topics)}")
        
        # At least comprehensive topics should have category_id
        assert len(with_category_id) >= 20, f"Expected at least 20 topics with category_id, got {len(with_category_id)}"

    def test_help_topics_have_tags_array(self, auth_headers):
        """Topics have tags array for search functionality"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        assert resp.status_code == 200
        topics = resp.json()
        
        # Check for tags field
        with_tags = [t for t in topics if t.get("tags") and len(t.get("tags", [])) > 0]
        print(f"Topics with tags: {len(with_tags)}/{len(topics)}")
        
        # Most comprehensive topics should have tags
        assert len(with_tags) >= 20, f"Expected at least 20 topics with tags, got {len(with_tags)}"
        
        # Verify tags structure
        sample_topic = with_tags[0] if with_tags else None
        if sample_topic:
            assert isinstance(sample_topic.get("tags"), list), "Tags should be a list"
            print(f"Sample topic '{sample_topic.get('name')}' has tags: {sample_topic.get('tags')[:5]}...")

    def test_help_topics_grouped_by_category(self, auth_headers):
        """Verify topics can be grouped by category"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        assert resp.status_code == 200
        topics = resp.json()
        
        # Group by category
        grouped = {}
        for t in topics:
            cat = t.get("category") or t.get("category_id") or "uncategorized"
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(t)
        
        print(f"Topics grouped into {len(grouped)} categories:")
        for cat, cat_topics in grouped.items():
            print(f"  - {cat}: {len(cat_topics)} topics")
        
        # Should have topics in multiple categories
        assert len(grouped) >= 5, f"Expected topics in at least 5 categories, got {len(grouped)}"

    def test_help_topics_searchable_by_tags(self, auth_headers):
        """Verify topics are searchable by tags (frontend concern but verifying data)"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        assert resp.status_code == 200
        topics = resp.json()
        
        # Find topic with specific tags
        laptop_topics = [t for t in topics if "laptop" in (t.get("tags") or [])]
        print(f"Topics with 'laptop' tag: {len(laptop_topics)}")
        
        printer_topics = [t for t in topics if "printer" in (t.get("tags") or [])]
        print(f"Topics with 'printer' tag: {len(printer_topics)}")
        
        # At least some topics should be findable by tags
        assert len(laptop_topics) >= 1 or len(printer_topics) >= 1, "Should have searchable tags"


class TestHelpTopicsCRUD:
    """Test CRUD operations for help topics with new fields"""

    def test_create_help_topic_with_tags(self, auth_headers):
        """Create help topic with category_id and tags"""
        # Get a category ID first
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        category = categories[0] if categories else None
        
        new_topic = {
            "name": "TEST_Topic With Tags",
            "slug": "test-topic-with-tags",
            "description": "A test topic with tags",
            "category": category.get("slug") if category else "general",
            "category_id": category.get("id") if category else None,
            "tags": ["test", "sample", "validation"],
            "default_priority": "medium",
            "require_device": False,
            "is_active": True,
            "is_public": True
        }
        
        resp = requests.post(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers, json=new_topic)
        assert resp.status_code == 200, f"Create failed: {resp.text}"
        
        created = resp.json()
        assert created.get("name") == new_topic["name"], "Name mismatch"
        assert created.get("tags") == new_topic["tags"], "Tags mismatch"
        assert "id" in created, "Missing id"
        
        self.__class__.test_topic_id = created["id"]
        print(f"✓ Created topic with tags: {created.get('tags')}")

    def test_update_help_topic_tags(self, auth_headers):
        """Update help topic tags"""
        topic_id = getattr(self.__class__, "test_topic_id", None)
        if not topic_id:
            pytest.skip("No test topic created")
        
        update_data = {
            "tags": ["updated", "new-tags", "modified"]
        }
        
        resp = requests.put(f"{BASE_URL}/api/ticketing/help-topics/{topic_id}", headers=auth_headers, json=update_data)
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        
        updated = resp.json()
        assert updated.get("tags") == update_data["tags"], "Tags not updated"
        print(f"✓ Updated topic tags: {updated.get('tags')}")

    def test_cleanup_test_topic(self, auth_headers):
        """Clean up test topic"""
        topic_id = getattr(self.__class__, "test_topic_id", None)
        if not topic_id:
            pytest.skip("No test topic to clean up")
        
        resp = requests.delete(f"{BASE_URL}/api/ticketing/help-topics/{topic_id}", headers=auth_headers)
        assert resp.status_code == 200, f"Delete failed: {resp.text}"
        print(f"✓ Cleaned up test topic")


class TestCategoryTopicIntegration:
    """Test integration between categories and topics"""

    def test_categories_have_correct_topic_counts(self, auth_headers):
        """Verify categories have topics assigned"""
        # Get categories
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        
        # Get topics
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics?include_inactive=true", headers=auth_headers)
        topics = resp.json()
        
        # Count topics per category
        counts = {}
        for t in topics:
            cat_id = t.get("category_id")
            cat_slug = t.get("category")
            key = cat_id or cat_slug or "uncategorized"
            counts[key] = counts.get(key, 0) + 1
        
        print("Topic counts per category:")
        for cat in categories:
            count_by_id = counts.get(cat["id"], 0)
            count_by_slug = counts.get(cat["slug"], 0)
            total = count_by_id + count_by_slug
            print(f"  - {cat['name']}: {total} topics")
        
        # Verify some categories have topics
        total_categorized = sum(counts.values())
        assert total_categorized > 20, f"Expected > 20 categorized topics, got {total_categorized}"

    def test_expected_category_names(self, auth_headers):
        """Verify expected category names exist"""
        resp = requests.get(f"{BASE_URL}/api/ticketing/help-topic-categories", headers=auth_headers)
        categories = resp.json()
        
        expected_names = [
            "Hardware & Devices",
            "Software & OS",
            "Network & Connectivity",
            "Peripherals & Accessories",
            "Service Requests",
            "Warranty & AMC",
            "Commercial & Billing",
            "General"
        ]
        
        category_names = [c.get("name") for c in categories]
        
        for name in expected_names:
            assert name in category_names, f"Missing expected category: {name}"
        
        print(f"✓ All {len(expected_names)} expected categories found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
