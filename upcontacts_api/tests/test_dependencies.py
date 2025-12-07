"""
Тесты для зависимостей (dependencies).
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from models import User
from auth.dependencies import get_current_user


class TestGetCurrentUser:  
    @patch('auth.dependencies.decode_token')
    @patch('auth.dependencies.get_cached_user')
    def test_get_current_user_from_cache(self, mock_cache, mock_decode, db_session):
        #Тест получения пользователя из кэша
        mock_decode.return_value = {"sub": "test@example.com"}
        mock_cache.return_value = {
            "id": 1,
            "email": "test@example.com",
            "is_verified": True,
            "avatar_url": None
        }
        
        user = get_current_user(token="valid_token", db=db_session)
        
        assert user.email == "test@example.com"
        assert user.id == 1
        assert user.is_verified is True
        mock_cache.assert_called_once_with("test@example.com")
    
    @patch('auth.dependencies.decode_token')
    @patch('auth.dependencies.get_cached_user')
    @patch('auth.dependencies.cache_user')
    def test_get_current_user_from_db(self, mock_cache_set, mock_cache_get, mock_decode, db_session):
        # Тест получения пользователя из БД и кэширования
        mock_decode.return_value = {"sub": "test@example.com"}
        mock_cache_get.return_value = None  # Не в кэше
        
        from auth.jwt_utils import get_password_hash
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        
        result = get_current_user(token="valid_token", db=db_session)
        
        assert result.email == "test@example.com"
        assert result.is_verified is True
        mock_cache_set.assert_called_once()
    
    @patch('auth.dependencies.decode_token')
    def test_get_current_user_invalid_token(self, mock_decode, db_session):
        # Тест с невалидным токеном
        mock_decode.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="invalid_token", db=db_session)
        
        assert exc.value.status_code == 401
        assert "Неверный токен" in exc.value.detail
    
    @patch('auth.dependencies.decode_token')
    def test_get_current_user_no_email_in_token(self, mock_decode, db_session):
        # Тест с токеном без email
        mock_decode.return_value = {"some": "data"}  # Нет "sub"
        
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="token_without_email", db=db_session)
        
        assert exc.value.status_code == 401
    
    @patch('auth.dependencies.decode_token')
    @patch('auth.dependencies.get_cached_user')
    def test_get_current_user_not_found(self, mock_cache, mock_decode, db_session):
        #Тест с несуществующим пользователем
        mock_decode.return_value = {"sub": "nonexistent@example.com"}
        mock_cache.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="valid_token", db=db_session)
        
        assert exc.value.status_code == 401
        assert "не найден" in exc.value.detail
    
    @patch('auth.dependencies.decode_token')
    @patch('auth.dependencies.get_cached_user')
    def test_get_current_user_not_verified(self, mock_cache, mock_decode, db_session):
        # Тест с неверифицированным пользователем
        mock_decode.return_value = {"sub": "unverified@example.com"}
        mock_cache.return_value = None
        
        from auth.jwt_utils import get_password_hash
        user = User(
            email="unverified@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=False
        )
        db_session.add(user)
        db_session.commit()
        
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="valid_token", db=db_session)
        
        assert exc.value.status_code == 403
        assert "не подтвержден" in exc.value.detail


class TestContactsDependencies:
    # Тесты для зависимостей контактов
    
    def test_get_user_for_contact(self):
        from contacts.dependencies import get_user_for_contact
        from auth.jwt_utils import get_password_hash
        
        mock_user = User(
            id=1,
            email="test@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=True
        )
        
        result = get_user_for_contact(current_user=mock_user)
        
        assert result == mock_user
        assert result.email == "test@example.com"
