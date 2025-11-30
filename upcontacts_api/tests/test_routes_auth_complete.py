"""
Функциональные тесты для всех маршрутов аутентификации и главных эндпоинтов.
"""
import pytest
from datetime import datetime, timedelta
from models import User
from auth.jwt_utils import get_password_hash
import secrets


class TestMainRoutes:
    """Тесты для основных эндпоинтов."""
    
    def test_root_endpoint(self, client):
        """Тест корневого эндпоинта."""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Contact Book API"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_health_check_redis_connected(self, client, mock_redis):
        """Тест health check с подключенным Redis."""
        # Arrange
        mock_redis.ping.return_value = True
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["redis"] == "connected"
    
    def test_health_check_redis_disconnected(self, client, mock_redis):
        """Тест health check с отключенным Redis."""
        # Arrange
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "disconnected"


class TestAuthRegistration:
    """Тесты для регистрации пользователей."""
    
    def test_register_success(self, client, mock_email):
        """Тест успешной регистрации."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "pass12"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert data["is_verified"] is False
        mock_email.assert_called_once()
    
    def test_register_duplicate_email(self, client, test_user, mock_email):
        """Тест регистрации с существующим email."""
        # Arrange
        user_data = {
            "email": test_user.email,
            "password": "pass12"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 409
        assert "уже существует" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        """Тест регистрации с невалидным email."""
        # Arrange
        user_data = {
            "email": "not-an-email",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 422
    
    def test_register_short_password(self, client):
        """Тест регистрации со слишком коротким паролем."""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "12345"  # < 6 символов
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 422


class TestEmailVerification:
    """Тесты для верификации email."""
    
    def test_verify_email_success(self, client, db_session):
        """Тест успешной верификации email."""
        # Arrange
        token = "valid_token_123"
        user = User(
            email="verify@example.com",
            hashed_password=get_password_hash("x"),
            is_verified=False,
            verification_token=token
        )
        db_session.add(user)
        db_session.commit()
        
        # Act
        response = client.get(f"/auth/verify-email?token={token}")
        
        # Assert
        assert response.status_code == 200
        assert "успешно подтвержден" in response.json()["detail"]
        
        # Verify in DB
        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None
    
    def test_verify_email_invalid_token(self, client):
        """Тест верификации с невалидным токеном."""
        # Act
        response = client.get("/auth/verify-email?token=invalid_token")
        
        # Assert
        assert response.status_code == 400
        assert "Неверный" in response.json()["detail"]
    
    def test_verify_email_already_verified(self, client, db_session):
        """Тест верификации уже подтвержденного email."""
        # Arrange
        token = "token_123"
        user = User(
            email="verified@example.com",
            hashed_password=get_password_hash("x"),
            is_verified=True,
            verification_token=token
        )
        db_session.add(user)
        db_session.commit()
        
        # Act
        response = client.get(f"/auth/verify-email?token={token}")
        
        # Assert
        assert response.status_code == 200
        assert "уже подтвержден" in response.json()["detail"]


class TestLogin:
    """Тесты для входа в систему."""
    
    def test_login_success(self, client, test_user):
        """Тест успешного входа."""
        # Act
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "test"}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Тест входа с неверным паролем."""
        # Act
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"}
        )
        
        # Assert
        assert response.status_code == 401
        assert "Неверный email или пароль" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        # Act
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"}
        )
        
        # Assert
        assert response.status_code == 401
    
    def test_login_unverified_user(self, client, db_session):
        """Тест входа с неподтвержденным email."""
        # Arrange
        user = User(
            email="unverified@example.com",
            hashed_password=get_password_hash("pass6"),
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Act
        response = client.post(
            "/auth/login",
            data={"username": "unverified@example.com", "password": "pass6"}
        )
        
        # Assert
        assert response.status_code == 403
        assert "не подтвержден" in response.json()["detail"]


class TestPasswordReset:
    """Тесты для сброса пароля."""
    
    def test_request_password_reset_existing_user(self, client, test_user, mock_email):
        """Тест запроса сброса пароля для существующего пользователя."""
        # Arrange
        reset_data = {"email": test_user.email}
        
        # Act
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        assert "письмо отправлено" in response.json()["detail"]
        mock_email.assert_called_once()
    
    def test_request_password_reset_nonexistent_user(self, client, mock_email):
        """Тест запроса сброса для несуществующего пользователя."""
        # Arrange
        reset_data = {"email": "nonexistent@example.com"}
        
        # Act
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        assert "письмо отправлено" in response.json()["detail"]
        mock_email.assert_not_called()
    
    def test_reset_password_success(self, client, db_session, test_user):
        """Тест успешного сброса пароля."""
        # Arrange
        reset_token = secrets.token_urlsafe(32)
        test_user.reset_token = reset_token
        test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "new123"
        }
        
        # Act
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 200
        assert "успешно изменен" in response.json()["detail"]
        
        # Verify password changed
        db_session.refresh(test_user)
        from auth.jwt_utils import verify_password
        assert verify_password("new123", test_user.hashed_password)
    
    def test_reset_password_invalid_token(self, client):
        """Тест сброса пароля с невалидным токеном."""
        # Arrange
        reset_data = {
            "token": "invalid_token",
            "new_password": "new123"
        }
        
        # Act
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 400
        assert "Неверный" in response.json()["detail"]
    
    def test_reset_password_expired_token(self, client, db_session, test_user):
        """Тест сброса пароля с истекшим токеном."""
        # Arrange
        reset_token = secrets.token_urlsafe(32)
        test_user.reset_token = reset_token
        test_user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "new123"
        }
        
        # Act
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert
        assert response.status_code == 400
        assert "истек" in response.json()["detail"]


class TestCurrentUser:
    """Тесты для получения текущего пользователя."""
    
    def test_get_me_success(self, client, auth_headers, test_user):
        """Тест получения информации о текущем пользователе."""
        # Act
        response = client.get("/auth/me", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert data["is_verified"] is True
    
    def test_get_me_unauthorized(self, client):
        """Тест получения информации без авторизации."""
        # Act
        response = client.get("/auth/me")
        
        # Assert
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self, client):
        """Тест получения информации с невалидным токеном."""
        # Act
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assert
        assert response.status_code == 401


class TestAvatarUpload:
    """Тесты для загрузки аватара."""
    
    @pytest.mark.skip(reason="Cloudinary интеграция требует реальных credentials")
    def test_upload_avatar_success(self, client, auth_headers, test_user):
        """Тест успешной загрузки аватара."""
        # Arrange
        from io import BytesIO
        fake_image = BytesIO(b"fake image content")
        files = {"file": ("avatar.jpg", fake_image, "image/jpeg")}
        
        # Act
        response = client.post(
            "/auth/upload-avatar",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
    
    def test_upload_avatar_unauthorized(self, client):
        """Тест загрузки аватара без авторизации."""
        # Arrange
        from io import BytesIO
        fake_image = BytesIO(b"fake image content")
        files = {"file": ("avatar.jpg", fake_image, "image/jpeg")}
        
        # Act
        response = client.post("/auth/upload-avatar", files=files)
        
        # Assert
        assert response.status_code == 401
    
    def test_upload_avatar_invalid_type(self, client, auth_headers):
        """Тест загрузки файла неверного типа."""
        # Arrange
        from io import BytesIO
        fake_file = BytesIO(b"not an image")
        files = {"file": ("document.pdf", fake_file, "application/pdf")}
        
        # Act
        response = client.post(
            "/auth/upload-avatar",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        assert "Поддерживаются только изображения" in response.json()["detail"]