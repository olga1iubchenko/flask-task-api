"""Tests for Flask Task API."""
import pytest
from app import app as flask_app
from models import db


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_tasks_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_task(client):
    response = client.post("/tasks", json={"title": "Buy milk", "description": "2% please"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == "Buy milk"
    assert data["completed"] is False


def test_get_task_not_found(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task(client):
    create = client.post("/tasks", json={"title": "Write tests"})
    task_id = create.get_json()["id"]
    response = client.put(f"/tasks/{task_id}", json={"completed": True})
    assert response.status_code == 200
    assert response.get_json()["completed"] is True


def test_delete_task(client):
    create = client.post("/tasks", json={"title": "Temporary task"})
    task_id = create.get_json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    # Verify it's gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_create_task_requires_title(client):
    response = client.post("/tasks", json={"description": "No title here"})
    assert response.status_code == 400, "Should reject task with no title"


def test_create_task_rejects_empty_title(client):
    response = client.post("/tasks", json={"title": "", "description": "Empty title"})
    assert response.status_code == 400


def test_create_task_rejects_whitespace_title(client):
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400


def test_create_task_rejects_no_json_body(client):
    response = client.post("/tasks", content_type="application/json", data="")
    assert response.status_code == 400
