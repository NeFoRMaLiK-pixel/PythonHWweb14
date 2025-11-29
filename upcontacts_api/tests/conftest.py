"""
Конфигурация pytest и фикстуры для тестов.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models import User, Contacts
from auth.jwt_utils import get_password_hash
import redis
from unittest.mock import Mock

# Тестовая БД в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Создает тестовую БД для каждого теста.
    
    Yields:
        Session: SQLAlchemy сессия
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Создает тестовый HTTP клиент FastAPI.
    
    Args:
        db_session: Фикстура БД
        
    Yields:
        TestClient: HTTP клиент для тестов
    """
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
    """
    Создает тестового пользователя в БД.
    
    Args:
        db_session: Фикстура БД
        
    Returns:
        User: Тестовый пользователь
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user):
    """
    Создает заголовки авторизации с JWT токеном.
    
    Args:
        client: HTTP клиент
        test_user: Тестовый пользователь
        
    Returns:
        dict: Заголовки с Authorization Bearer токеном
    """
    response = client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "testpassword"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_contact(db_session, test_user):
    """
    Создает тестовый контакт в БД.
    
    Args:
        db_session: Фикстура БД
        test_user: Тестовый пользователь
        
    Returns:
        Contacts: Тестовый контакт
    """
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


@pytest.fixture
def mock_redis(monkeypatch):
    """
    Мокает Redis клиент для тестов.
    
    Args:
        monkeypatch: pytest monkeypatch фикстура
    """
    mock = Mock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    monkeypatch.setattr("redis_client.redis_client", mock)
    return mock


@pytest.fixture
def mock_email(monkeypatch):
    """
    Мокает отправку email для тестов.
    
    Args:
        monkeypatch: pytest monkeypatch фикстура
    """
    mock = Mock()
    monkeypatch.setattr("email_utils.fm.send_message", mock)
    return mock