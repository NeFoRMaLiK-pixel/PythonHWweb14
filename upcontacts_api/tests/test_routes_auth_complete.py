# Функциональные тесты для всех маршрутов аутентификации и главных эндпоинтов.

import pytest
from datetime import datetime, timedelta
from models import User
from auth.jwt_utils import get_password_hash
import secrets


class TestMainRoutes:
    
    def test_root_endpoint(self, client):
        #Тест корневого эндпоинта
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Contact Book API"
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_health_check_redis_connected(self, client, mock_redis):
        # Тест health check с подключенным Redis

        mock_redis.ping.return_value = True
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["redis"] == "connected"
    
    def test_health_check_redis_disconnected(self, client, mock_redis):
        # Тест health check с отключенным Redis
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["redis"] == "disconnected"


class TestAuthRegistration:
    
    def test_register_success(self, client, mock_email):
        # Тест успешной регистрации
        user_data = {
            "email": "newuser@example.com",
            "password": "pass12"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert data["is_verified"] is False
        mock_email.assert_called_once()
    
    def test_register_duplicate_email(self, client, test_user, mock_email):
        # Тест регистрации с существующим email
        user_data = {
            "email": test_user.email,
            "password": "pass12"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 409
        assert "уже существует" in response.json()["detail"]
    
    def test_register_invalid_email(self, client):
        # Тест регистрации с невалидным email
        user_data = {
            "email": "not-an-email",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_register_short_password(self, client):
        # Тест регистрации со слишком коротким паролем
        user_data = {
            "email": "test@example.com",
            "password": "12345"  # < 6 символов
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422


class TestEmailVerification:
    
    def test_verify_email_success(self, client, db_session):
        # Тест успешной верификации email
        token = "valid_token_123"
        user = User(
            email="verify@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=False,
            verification_token=token
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get(f"/auth/verify-email?token={token}")
        
        assert response.status_code == 200
        assert "успешно подтвержден" in response.json()["detail"]
        
        db_session.refresh(user)
        assert user.is_verified is True
        assert user.verification_token is None
    
    def test_verify_email_invalid_token(self, client):
        # Тест верификации с невалидным токеном
        response = client.get("/auth/verify-email?token=invalid_token")
        
        assert response.status_code == 400
        assert "Неверный" in response.json()["detail"]
    
    def test_verify_email_already_verified(self, client, db_session):
        # Тест верификации уже подтвержденного email
        token = "token_123"
        user = User(
            email="verified@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=True,
            verification_token=token
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.get(f"/auth/verify-email?token={token}")
        
        assert response.status_code == 200
        assert "уже подтвержден" in response.json()["detail"]


class TestLogin:
    
    def test_login_success(self, client, test_user):
        # Тест успешного входа
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpass"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        # Тест входа с неверным паролем
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert "Неверный email или пароль" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        # Тест входа несуществующего пользователя
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"}
        )
        
        assert response.status_code == 401
    
    def test_login_unverified_user(self, client, db_session):
        # Тест входа с неподтвержденным email
        user = User(
            email="unverified@example.com",
            hashed_password=get_password_hash("pass6"),
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/auth/login",
            data={"username": "unverified@example.com", "password": "pass6"}
        )
        
        assert response.status_code == 403
        assert "не подтвержден" in response.json()["detail"]


class TestPasswordReset:
    
    def test_request_password_reset_existing_user(self, client, test_user, mock_email):
        # Тест запроса сброса пароля для существующего пользователя
        reset_data = {"email": test_user.email}
        
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        assert response.status_code == 200
        assert "письмо отправлено" in response.json()["detail"]
        mock_email.assert_called_once()
    
    def test_request_password_reset_nonexistent_user(self, client, mock_email):
        # Тест запроса сброса для несуществующего пользователя
        reset_data = {"email": "nonexistent@example.com"}
        
        response = client.post("/auth/request-password-reset", json=reset_data)
        
        assert response.status_code == 200
        assert "письмо отправлено" in response.json()["detail"]
        mock_email.assert_not_called()
    
    def test_reset_password_success(self, client, db_session, test_user):
        # Тест успешного сброса пароля
        reset_token = secrets.token_urlsafe(32)
        test_user.reset_token = reset_token
        test_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "new123"
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 200
        assert "успешно изменен" in response.json()["detail"]
        
        db_session.refresh(test_user)
        from auth.jwt_utils import verify_password
        assert verify_password("new123", test_user.hashed_password)
    
    def test_reset_password_invalid_token(self, client):
        # Тест сброса пароля с невалидным токеном
        reset_data = {
            "token": "invalid_token",
            "new_password": "new123"
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
        assert "Неверный" in response.json()["detail"]
    
    def test_reset_password_expired_token(self, client, db_session, test_user):
        # Тест сброса пароля с истекшим токеном
        reset_token = secrets.token_urlsafe(32)
        test_user.reset_token = reset_token
        test_user.reset_token_expires = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()
        
        reset_data = {
            "token": reset_token,
            "new_password": "new123"
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        assert response.status_code == 400
        assert "истек" in response.json()["detail"]


class TestCurrentUser:
    
    def test_get_me_success(self, client, auth_headers, test_user):
        # Тест получения информации о текущем пользователе
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert data["is_verified"] is True
    
    def test_get_me_unauthorized(self, client):
        # Тест получения информации без авторизации
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self, client):
        # Тест получения информации с невалидным токеном

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

class TestAvatarUpload:
    
    @pytest.mark.skip(reason="Cloudinary интеграция требует реальных credentials")
    def test_upload_avatar_success(self, client, auth_headers, test_user):
        # Тест успешной загрузки аватара
        from io import BytesIO
        fake_image = BytesIO(b"fake image content")
        files = {"file": ("avatar.jpg", fake_image, "image/jpeg")}
        
        response = client.post(
            "/auth/upload-avatar",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
    
    def test_upload_avatar_unauthorized(self, client):
        # Тест загрузки аватара без авторизации
        from io import BytesIO
        fake_image = BytesIO(b"fake image content")
        files = {"file": ("avatar.jpg", fake_image, "image/jpeg")}
        
        response = client.post("/auth/upload-avatar", files=files)
        
        assert response.status_code == 401
    
    def test_upload_avatar_invalid_type(self, client, auth_headers):
        # Тест загрузки файла неверного типа
        from io import BytesIO
        fake_file = BytesIO(b"not an image")
        files = {"file": ("document.pdf", fake_file, "application/pdf")}
        
        response = client.post(
            "/auth/upload-avatar",
            files=files,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Поддерживаются только изображения" in response.json()["detail"]