import copy
import pytest
from fastapi.testclient import TestClient
from app import app, activities


# Store a snapshot of the original activities state
_original_activities = copy.deepcopy(activities)


@pytest.fixture()
def client():
    """Yield a TestClient and restore activities state after each test."""
    yield TestClient(app)
    # Teardown: reset activities to original state
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


def test_root_redirects(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all(client):
    # Arrange
    expected_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert response.status_code == 200
    assert len(data) == 9
    for name, details in data.items():
        assert expected_keys.issubset(details.keys()), f"{name} missing keys"


def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "test@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_nonexistent_activity(client):
    # Arrange
    activity_name = "Nonexistent"
    email = "test@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # already a participant

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Already signed up for this activity"
