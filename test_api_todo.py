import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from todo_app.app.database import Base, get_db
from todo_app.app.api import app

engine = create_engine("sqlite:///todo_app/data/test_todo.db")
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_and_login(setup_db):
    """Тест регистрации и логина."""
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123"
    })
    assert response.status_code == 200

    response = client.post("/auth", json={
        "username": "testuser",
        "password": "test123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_create_and_get_todo_items(setup_db):
    """Тест создания и получения задач."""
    client.post("/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "pass123"
    })

    login = client.post("/auth", json={
        "username": "user1",
        "password": "pass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/items/", headers=headers, json={
        "title": "Сделать дз",
        "completed": False
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Сделать дз"

    response = client.get("/items/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_my_items_filter(setup_db):
    """Тест фильтрации моих задач."""
    client.post("/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "pass123"
    })

    login = client.post("/auth", json={
        "username": "user2",
        "password": "pass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/items/", headers=headers, json={"title": "Задача 1", "completed": False})
    client.post("/items/", headers=headers, json={"title": "Задача 2", "completed": True})

    response = client.get("/items/my/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/items/my/?completed=true", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["completed"] is True

    response = client.get("/items/my/?completed=false", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["completed"] is False


def test_update_and_delete_item(setup_db):
    """Тест обновления и удаления задачи."""
    client.post("/register", json={
        "username": "user3",
        "email": "user3@example.com",
        "password": "pass123"
    })

    login = client.post("/auth", json={
        "username": "user3",
        "password": "pass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post("/items/", headers=headers, json={
        "title": "Исходная задача",
        "completed": False
    })
    item_id = create_resp.json()["id"]

    update_resp = client.put(f"/items/{item_id}", headers=headers, json={
        "title": "Обновленная задача",
        "completed": True
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Обновленная задача"
    assert update_resp.json()["completed"] is True

    delete_resp = client.delete(f"/items/{item_id}", headers=headers)
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/items/{item_id}", headers=headers)
    assert get_resp.status_code == 404


