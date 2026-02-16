import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    yield
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"]


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_have_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_have_correct_participant_counts(self, client):
        """Test that participant counts match expected values"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up a duplicate participant fails"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_to_nonexistent_activity_fails(self, client):
        """Test that signing up to non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_adds_to_participants_list(self, client):
        """Test that signup correctly adds participant to list"""
        # Sign up new participant
        client.post(
            "/activities/Programming%20Class/signup?email=newstudent@mergington.edu"
        )
        
        # Verify in activities list
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Programming Class"]["participants"]
        assert len(data["Programming Class"]["participants"]) == 3


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering non-existent participant fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_removes_from_participants_list(self, client):
        """Test that unregister correctly removes from list"""
        # Get initial count
        get_response = client.get("/activities")
        initial_count = len(get_response.json()["Tennis Club"]["participants"])
        
        # Unregister a participant
        client.delete(
            "/activities/Tennis%20Club/unregister?email=alex@mergington.edu"
        )
        
        # Verify count decreased
        get_response = client.get("/activities")
        new_count = len(get_response.json()["Tennis Club"]["participants"])
        assert new_count == initial_count - 1
        assert "alex@mergington.edu" not in get_response.json()["Tennis Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
