"""
Конфигурация pytest и фикстуры для тестов.
"""
import sys
import os

# ✅ КРИТИЧНО: добавляем текущую директорию в путь
sys.path.insert(0, os.path.abspath('.'))

# ✅ Переменные окружения ПЕРЕД любыми импортами
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_key_12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
os.environ["REDIS_HOST"] = "localhost"
os.environ["REDIS_PORT"] = "6379"

# ✅ Чистим кэш модулей
for mod in ['database', 'models', 'main']:
    if mod in sys.modules:
        del sys.modules[mod]

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, AsyncMock

# Создаём тестовый engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

import database
database.engine = test_engine
database.SessionLocal = TestingSessionLocal

from database import Base, get_db
from models import User, Contacts
from auth.jwt_utils import get_password_hash
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    # Создаёт таблицы перед каждым тестом
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(setup_test_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    # Создает тестовый HTTP клиент FastAPI
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    # Создает тестового пользователя
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """Создает заголовки авторизации."""
    response = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_contact(db_session, test_user):
    # Создает тестовый контакт
    from datetime import date
    contact = Contacts(
        name="John",
        surname="Doe",
        email="john@example.com",
        phone="+380501234567",
        birthday=date(1990, 1, 1),
        user_id=test_user.id
    )
    db_session.add(contact)
    db_session.commit()
    db_session.refresh(contact)
    return contact


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    # Мокает Redis клиент
    mock = Mock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    mock.ping.return_value = True
    monkeypatch.setattr("redis_client.redis_client", mock)
    return mock


@pytest.fixture(autouse=True)
def mock_email(monkeypatch):
    # Мокает отправку email
    mock = AsyncMock()
    monkeypatch.setattr("email_utils.fm.send_message", mock)
    return mock