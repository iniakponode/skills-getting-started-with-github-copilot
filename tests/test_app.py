"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
from copy import deepcopy


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store a deep copy of the original state
    original_activities = deepcopy(activities)
    
    yield
    
    # Reset to original state
    activities.clear()
    activities.update(original_activities)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_with_special_characters_in_name(self, client):
        """Test signup with URL-encoded activity name"""
        response = client.post(
            "/activities/Art%20Studio%20Workshop/signup?email=newartist@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newartist@mergington.edu" in activities_data["Art Studio Workshop"]["participants"]
    
    def test_signup_activity_at_capacity(self, client):
        """Test that signup fails when activity is at max capacity"""
        # Fill up Chess Club (max 12 participants, currently has 2)
        for i in range(10):
            response = client.post(
                f"/activities/Chess Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to add one more beyond capacity
        response = client.post(
            "/activities/Chess Club/signup?email=rejected@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()
    
    def test_signup_empty_email(self, client):
        """Test signup with empty email"""
        response = client.post("/activities/Chess Club/signup?email=")
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
        data = response.json()
        assert "email" in data["detail"].lower()
    
    def test_signup_invalid_email_format(self, client):
        """Test signup with invalid email format"""
        response = client.post("/activities/Chess Club/signup?email=notanemail")
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
    
    def test_signup_missing_at_symbol(self, client):
        """Test signup with email missing @ symbol"""
        response = client.post("/activities/Chess Club/signup?email=invalidemail.com")
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
        data = response.json()
        assert "email" in data["detail"].lower()
    
    def test_signup_missing_email(self, client):
        """Test signup with missing email query parameter"""
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422  # FastAPI returns 422 for missing required parameters


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered_participant(self, client):
        """Test unregistering a student who isn't registered"""
        email = "notregistered@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student not registered for this activity"
    
    def test_unregister_with_special_characters_in_name(self, client):
        """Test unregister with URL-encoded activity name"""
        email = "jackson@mergington.edu"  # Already in Art Studio Workshop
        response = client.delete(
            f"/activities/Art%20Studio%20Workshop/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Art Studio Workshop"]["participants"]
    
    def test_unregister_empty_email(self, client):
        """Test unregister with empty email"""
        response = client.delete("/activities/Chess Club/unregister?email=")
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()
    
    def test_unregister_invalid_email_format(self, client):
        """Test unregister with invalid email format"""
        response = client.delete("/activities/Chess Club/unregister?email=notanemail")
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()


class TestIntegrationScenarios:
    """Integration tests for common user workflows"""
    
    def test_signup_and_unregister_workflow(self, client):
        """Test complete workflow of signing up and then unregistering"""
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        final_response = client.get("/activities")
        final_data = final_response.json()
        assert email not in final_data[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multitasker@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Chess Club", "Programming Class", "Drama Club"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify student is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
