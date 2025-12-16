# test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from shorturl_app.app.database import Base, get_db
from shorturl_app.app.api import app

engine = create_engine("sqlite:///shorturl_app/data/test_shorturl.db")
TestingSessionLocal = sessionmaker(bind=engine)


def override_get_db():
    """Переопределяем зависимость базы данных для тестов"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_db():
    """Фикстура для создания и очистки базы данных перед каждым тестом"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint():
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "URL Shortener Service"
    assert "documentation" in data
    assert "endpoints" in data


def test_create_short_url(setup_db):
    """Тест создания короткой ссылки"""
    test_url = "https://example.com/very/long/path"

    response = client.post("/shorten", json={"url": test_url})

    assert response.status_code == 200
    data = response.json()

    assert "short_id" in data
    assert data["original_url"] == test_url
    assert "short_url" in data
    assert data["clicks"] == 0
    assert len(data["short_id"]) == 6

    # Проверяем, что URL добавляется в short_url
    assert data["short_id"] in data["short_url"]


def test_create_short_url_without_protocol(setup_db):
    """Тест создания короткой ссылки без указания протокола"""
    response = client.post("/shorten", json={"url": "example.com"})

    assert response.status_code == 200
    data = response.json()

    # Проверяем, что протокол был добавлен автоматически
    assert data["original_url"] == "http://example.com"


def test_create_duplicate_url(setup_db):
    """Тест создания дубликата URL (должен вернуть существующую ссылку)"""
    test_url = "https://duplicate.example.com"

    response1 = client.post("/shorten", json={"url": test_url})
    assert response1.status_code == 200
    data1 = response1.json()
    first_short_id = data1["short_id"]

    response2 = client.post("/shorten", json={"url": test_url})
    assert response2.status_code == 200
    data2 = response2.json()

    assert data2["short_id"] == first_short_id


def test_redirect_to_original_url(setup_db):
    """Тест перенаправления по короткой ссылке"""
    create_response = client.post("/shorten", json={"url": "https://redirect-test.example.com"})
    short_id = create_response.json()["short_id"]

    response = client.get(f"/{short_id}", follow_redirects=False)

    assert response.status_code in [302, 307, 308]
    assert "location" in response.headers
    assert response.headers["location"] == "https://redirect-test.example.com"


def test_redirect_nonexistent_url(setup_db):
    """Тест редиректа несуществующей ссылки"""
    response = client.get("/nonexistent", follow_redirects=False)

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Ссылка не найдена" in data["detail"]


def test_get_url_statistics(setup_db):
    """Тест получения статистики по короткой ссылке"""
    create_response = client.post("/shorten", json={"url": "https://stats-test.example.com"})
    short_id = create_response.json()["short_id"]

    response = client.get(f"/stats/{short_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["short_id"] == short_id
    assert data["original_url"] == "https://stats-test.example.com"
    assert data["clicks"] == 0
    assert data["is_active"] is True

    client.get(f"/{short_id}", follow_redirects=False)
    client.get(f"/{short_id}", follow_redirects=False)

    response = client.get(f"/stats/{short_id}")
    data = response.json()
    assert data["clicks"] == 2


def test_get_statistics_nonexistent_url(setup_db):
    """Тест получения статистики несуществующей ссылки"""
    response = client.get("/stats/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Ссылка не найдена" in data["detail"]


def test_delete_short_url(setup_db):
    """Тест удаления короткой ссылки"""
    create_response = client.post("/shorten", json={"url": "https://delete-test.example.com"})
    short_id = create_response.json()["short_id"]

    redirect_response = client.get(f"/{short_id}", follow_redirects=False)
    assert redirect_response.status_code in [302, 307, 308]

    delete_response = client.delete(f"/{short_id}")
    assert delete_response.status_code == 200
    delete_data = delete_response.json()

    assert delete_data["message"] == "Ссылка успешно удалена"
    assert delete_data["short_id"] == short_id

    redirect_response = client.get(f"/{short_id}", follow_redirects=False)
    assert redirect_response.status_code == 404

    stats_response = client.get(f"/stats/{short_id}")
    assert stats_response.status_code == 404


def test_delete_nonexistent_url(setup_db):
    """Тест удаления несуществующей ссылки"""
    response = client.delete("/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Ссылка не найдена" in data["detail"]


def test_recreate_after_deletion(setup_db):
    """Тест повторного создания ссылки после удаления"""
    test_url = "https://recreate-test.example.com"

    create_response1 = client.post("/shorten", json={"url": test_url})
    short_id1 = create_response1.json()["short_id"]

    client.delete(f"/{short_id1}")

    create_response2 = client.post("/shorten", json={"url": test_url})
    short_id2 = create_response2.json()["short_id"]

    assert short_id1 != short_id2


def test_short_id_generation_uniqueness(setup_db):
    """Тест уникальности генерации short_id"""
    short_ids = set()

    for i in range(10):
        response = client.post("/shorten", json={"url": f"https://test{i}.example.com"})
        short_id = response.json()["short_id"]
        short_ids.add(short_id)

    assert len(short_ids) == 10


def test_invalid_url_format(setup_db):
    """Тест создания ссылки с невалидным URL"""
    response = client.post("/shorten", json={"url": ""})
    assert response.status_code == 200


def test_api_documentation_endpoints():
    """Тест доступности документации API"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200