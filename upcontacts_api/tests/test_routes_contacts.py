"""
Функциональные тесты для маршрутов контактов (pytest).
"""
import pytest
from datetime import date


class TestContactsRoutes:
    """Функциональные тесты для CRUD операций с контактами."""
    
    def test_create_contact_success(self, client, auth_headers):
        """Тест успешного создания контакта."""
        # Arrange
        contact_data = {
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01",
            "extra": "Friend"
        }
        
        # Act
        response = client.post("/contacts/", json=contact_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John"
        assert data["email"] == "john@example.com"
        assert "id" in data
    
    def test_create_contact_unauthorized(self, client):
        """Тест создания контакта без авторизации."""
        # Arrange
        contact_data = {
            "name": "John",
            "surname": "Doe",
            "email": "john@example.com",
            "phone": "+380501234567",
            "birthday": "1990-01-01"
        }
        
        # Act
        response = client.post("/contacts/", json=contact_data)
        
        # Assert
        assert response.status_code == 401
    
    def test_create_contact_invalid_email(self, client, auth_headers):
        """Тест создания контакта с невалидным email."""
        # Arrange
        contact_data = {
            "name": "John",
            "surname": "Doe",
            "email": "invalid-email",
            "phone": "+380501234567",
            "birthday": "1990-01-01"
        }
        
        # Act
        response = client.post("/contacts/", json=contact_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == 422
    
    def test_get_contacts_empty(self, client, auth_headers):
        """Тест получения пустого списка контактов."""
        # Act
        response = client.get("/contacts/", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_contacts_list(self, client, auth_headers, test_contact):
        """Тест получения списка контактов."""
        # Act
        response = client.get("/contacts/", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == test_contact.name
    
    def test_get_contact_by_id(self, client, auth_headers, test_contact):
        """Тест получения контакта по ID."""
        # Act
        response = client.get(f"/contacts/{test_contact.id}", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_contact.id
        assert data["name"] == test_contact.name
    
    def test_get_contact_not_found(self, client, auth_headers):
        """Тест получения несуществующего контакта."""
        # Act
        response = client.get("/contacts/999", headers=auth_headers)
        
        # Assert
        assert response.status_code == 404
    
    def test_update_contact(self, client, auth_headers, test_contact):
        """Тест обновления контакта."""
        # Arrange
        update_data = {
            "phone": "+380509999999",
            "extra": "Best friend"
        }
        
        # Act
        response = client.put(
            f"/contacts/{test_contact.id}",
            json=update_data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+380509999999"
        assert data["extra"] == "Best friend"
    
    def test_delete_contact(self, client, auth_headers, test_contact):
        """Тест удаления контакта."""
        # Act
        response = client.delete(f"/contacts/{test_contact.id}", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["detail"] == "Контакт удалён"
        
        # Verify deletion
        get_response = client.get(f"/contacts/{test_contact.id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_search_contacts(self, client, auth_headers, test_contact):
        """Тест поиска контактов."""
        # Act
        response = client.get("/contacts/search/?query=John", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "John"
    
    def test_search_contacts_no_results(self, client, auth_headers):
        """Тест поиска без результатов."""
        # Act
        response = client.get("/contacts/search/?query=Nonexistent", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        assert response.json() == []


class TestAuthRoutes:
    """Функциональные тесты для аутентификации."""
    
    def test_register_success(self, client, mock_email):
        """Тест успешной регистрации."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
    
    def test_register_duplicate_email(self, client, test_user, mock_email):
        """Тест регистрации с существующим email."""
        # Arrange
        user_data = {
            "email": test_user.email,
            "password": "password123"
        }
        
        # Act
        response = client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 409
    
    def test_login_success(self, client, test_user):
        """Тест успешного входа."""
        # Act
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword"}
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
    
    def test_login_nonexistent_user(self, client):
        """Тест входа несуществующего пользователя."""
        # Act
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com", "password": "password"}
        )
        
        # Assert
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers, test_user):
        """Тест получения текущего пользователя."""
        # Act
        response = client.get("/auth/me", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email