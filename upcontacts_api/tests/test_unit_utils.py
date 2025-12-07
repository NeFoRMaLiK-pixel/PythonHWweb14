# Юнит-тесты для утилит JWT Redis Email Cloudinary.

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import json


class TestJWTHandler(unittest.TestCase):
    
    @patch('auth.jwt_handler.jwt.encode')
    def test_create_access_token(self, mock_encode):
        # Тест создания access токена
        from auth.jwt_handler import create_access_token
        
        mock_encode.return_value = "test_token"
        data = {"sub": "test@example.com"}
        
        token = create_access_token(data)
        
        self.assertEqual(token, "test_token")
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args[0]
        self.assertEqual(call_args[0]["sub"], "test@example.com")
        self.assertIn("exp", call_args[0])
    
    @patch('auth.jwt_handler.jwt.encode')
    def test_create_refresh_token(self, mock_encode):
        # Тест создания refresh токена
        from auth.jwt_handler import create_refresh_token
        
        mock_encode.return_value = "refresh_token"
        data = {"sub": "test@example.com"}
        
        token = create_refresh_token(data)
        
        self.assertEqual(token, "refresh_token")
        mock_encode.assert_called_once()
    
    @patch('auth.jwt_handler.jwt.decode')
    def test_decode_token_success(self, mock_decode):
        # Тест успешной расшифровки токена
        from auth.jwt_handler import decode_token
        
        expected_payload = {"sub": "test@example.com", "exp": 1234567890}
        mock_decode.return_value = expected_payload
        
        payload = decode_token("valid_token")
        
        self.assertEqual(payload, expected_payload)
        mock_decode.assert_called_once()
    
    @patch('auth.jwt_handler.jwt.decode')
    def test_decode_token_invalid(self, mock_decode):
        # Тест расшифровки невалидного токена
        from auth.jwt_handler import decode_token
        from jose import JWTError
        
        mock_decode.side_effect = JWTError("Invalid token")
        
        payload = decode_token("invalid_token")
        
        self.assertIsNone(payload)


class TestJWTUtils(unittest.TestCase):
    
    def test_get_password_hash(self):
        # Тест хеширования пароля
        from auth.jwt_utils import get_password_hash
        
        hashed = get_password_hash("pass")
        
        self.assertIsNotNone(hashed)
        self.assertNotEqual(hashed, "x")
        self.assertTrue(hashed.startswith("$2b$"))
    
    def test_verify_password_correct(self):
        # Тест проверки правильного пароля
        from auth.jwt_utils import get_password_hash, verify_password
        
        password = "x"
        hashed = get_password_hash(password)
        
        result = verify_password(password, hashed)
        
        self.assertTrue(result)
    
    def test_verify_password_incorrect(self):
        # Тест проверки неправильного пароля
        from auth.jwt_utils import get_password_hash, verify_password
        
        hashed = get_password_hash("pass")
        
        result = verify_password("y", hashed)
        
        self.assertFalse(result)
    
    def test_get_user_by_email(self):
        # Тест получения пользователя по email
        from auth.jwt_utils import get_user_by_email
        from models import User
        
        mock_db = MagicMock()
        mock_user = User(id=1, email="test@example.com")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        user = get_user_by_email(mock_db, "test@example.com")
        
        self.assertEqual(user.email, "test@example.com")
        mock_db.query.assert_called_once()


class TestRedisClient(unittest.TestCase):
    
    @patch('redis_client.redis_client')
    def test_cache_user(self, mock_redis):
        # Тест кэширования пользователя
        from redis_client import cache_user
        
        user_data = {"id": 1, "email": "test@example.com"}
        mock_redis.setex.return_value = True
        
        cache_user("test@example.com", user_data, expire=3600)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        self.assertEqual(call_args[0], "user:test@example.com")
        self.assertEqual(call_args[1], 3600)
        self.assertEqual(json.loads(call_args[2]), user_data)
    
    @patch('redis_client.redis_client')
    def test_get_cached_user_exists(self, mock_redis):
        # Тест получения существующего кэша
        from redis_client import get_cached_user
        
        user_data = {"id": 1, "email": "test@example.com"}
        mock_redis.get.return_value = json.dumps(user_data)
        
        result = get_cached_user("test@example.com")
        
        self.assertEqual(result, user_data)
        mock_redis.get.assert_called_once_with("user:test@example.com")
    
    @patch('redis_client.redis_client')
    def test_get_cached_user_not_exists(self, mock_redis):
        # Тест получения несуществующего кэша
        from redis_client import get_cached_user
        
        mock_redis.get.return_value = None
        
        result = get_cached_user("test@example.com")
        
        self.assertIsNone(result)
    
    @patch('redis_client.redis_client')
    def test_delete_cached_user(self, mock_redis):
        # Тест удаления кэша пользователя
        from redis_client import delete_cached_user
        
        mock_redis.delete.return_value = 1
        
        delete_cached_user("test@example.com")
        
        mock_redis.delete.assert_called_once_with("user:test@example.com")
    
    @patch('redis_client.redis_client')
    def test_redis_connection_success(self, mock_redis):
        # Тест успешного подключения к Redis
        from redis_client import test_redis_connection
        
        mock_redis.ping.return_value = True
        
        result = test_redis_connection()
        
        self.assertTrue(result)
        mock_redis.ping.assert_called_once()
    
    @patch('redis_client.redis_client')
    def test_redis_connection_failure(self, mock_redis):
        # Тест неудачного подключения к Redis
        from redis_client import test_redis_connection
        
        mock_redis.ping.side_effect = Exception("Connection error")
        
        result = test_redis_connection()
        
        self.assertFalse(result)


class TestEmailUtils(unittest.IsolatedAsyncioTestCase):
    
    @patch('email_utils.fm.send_message')
    async def test_send_verification_email(self, mock_send):
        # Тест отправки письма верификации
        from email_utils import send_verification_email
        
        mock_send.return_value = AsyncMock()
        
        await send_verification_email("test@example.com", "token123")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args.subject, "Подтверждение email")
        self.assertTrue(any("test@example.com" in str(r) for r in call_args.recipients))
        self.assertIn("token123", call_args.body)
    
    @patch('email_utils.fm.send_message')
    async def test_send_reset_password_email(self, mock_send):
        # Тест отправки письма сброса пароля
        from email_utils import send_reset_password_email
        
        mock_send.return_value = AsyncMock()
        
        await send_reset_password_email("test@example.com", "reset_token")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args.subject, "Сброс пароля")
        self.assertTrue(any("test@example.com" in str(r) for r in call_args.recipients))
        self.assertIn("reset_token", call_args.body)


class TestCloudinaryUtils(unittest.TestCase):
    
    @patch('cloudinary_utils.cloudinary.uploader.upload')
    def test_upload_avatar_success(self, mock_upload):
        # Тест успешной загрузки аватара
        from cloudinary_utils import upload_avatar
        
        mock_upload.return_value = {"secure_url": "https://cloudinary.com/avatar.jpg"}
        file_content = b"fake_image_data"
        
        url = upload_avatar(file_content, "user_123")
        
        self.assertEqual(url, "https://cloudinary.com/avatar.jpg")
        mock_upload.assert_called_once()
        call_kwargs = mock_upload.call_args[1]
        self.assertEqual(call_kwargs["folder"], "avatars")
        self.assertEqual(call_kwargs["public_id"], "user_user_123")
    
    @patch('cloudinary_utils.cloudinary.uploader.upload')
    def test_upload_avatar_failure(self, mock_upload):
        # Тест ошибки загрузки аватара
        from cloudinary_utils import upload_avatar
        
        mock_upload.side_effect = Exception("Upload failed")
        
        with self.assertRaises(Exception) as context:
            upload_avatar(b"data", "user_123")
        
        self.assertIn("Ошибка загрузки в Cloudinary", str(context.exception))
    
    @patch('cloudinary_utils.cloudinary.uploader.destroy')
    def test_delete_avatar(self, mock_destroy):
        # Тест удаления аватара
        from cloudinary_utils import delete_avatar
        
        mock_destroy.return_value = {"result": "ok"}
        
        delete_avatar("user_123")
        
        mock_destroy.assert_called_once_with("avatars/user_user_123")


if __name__ == '__main__':
    unittest.main()
