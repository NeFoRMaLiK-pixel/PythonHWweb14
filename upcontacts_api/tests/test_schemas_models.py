# Тесты для схем Pydantic и моделей SQLAlchemy

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from schemas import (
    ContactCreate, ContactUpdate, ContactOut,
    UserCreate, UserOut, Token, EmailVerification,
    PasswordResetRequest, PasswordReset, Message
)


class TestContactSchemas:
    
    def test_contact_create_valid(self):
        # Тест валидной схемы создания контакта
        contact = ContactCreate(
            name="John",
            surname="Doe",
            email="john@example.com",
            phone="+380501234567",
            birthday=date(1990, 1, 1),
            extra="Friend"
        )
        
        assert contact.name == "John"
        assert contact.email == "john@example.com"
        assert contact.phone == "+380501234567"
    
    def test_contact_create_invalid_email(self):
        # Тест невалидного email
        with pytest.raises(ValidationError):
            ContactCreate(
                name="John",
                surname="Doe",
                email="not-an-email",
                phone="+380501234567",
                birthday=date(1990, 1, 1)
            )
    
    def test_contact_create_invalid_phone(self):
        #Тест невалидного телефона
        with pytest.raises(ValidationError):
            ContactCreate(
                name="John",
                surname="Doe",
                email="john@example.com",
                phone="123", 
                birthday=date(1990, 1, 1)
            )
    
    def test_contact_create_name_too_short(self):
        # Тест слишком короткого имени
        with pytest.raises(ValidationError):
            ContactCreate(
                name="",  
                surname="Doe",
                email="john@example.com",
                phone="+380501234567",
                birthday=date(1990, 1, 1)
            )
    
    def test_contact_update_partial(self):
        # Тест частичного обновления контакта
        update = ContactUpdate(phone="+380509999999")
        
        # Assert
        assert update.phone == "+380509999999"
        assert update.name is None
        assert update.email is None
    
    def test_contact_out_serialization(self, test_contact):
        # Тест сериализации ContactOut
        contact_out = ContactOut.model_validate(test_contact)
        
        assert contact_out.id == test_contact.id
        assert contact_out.name == test_contact.name
        assert contact_out.email == test_contact.email


class TestUserSchemas:
    # Тесты для схем пользователей
    
    def test_user_create_valid(self):
        # Тест валидной схемы создания пользователя
        user = UserCreate(
            email="test@example.com",
            password="password123"
        )
        
        assert user.email == "test@example.com"
        assert user.password == "password123"
    
    def test_user_create_invalid_email(self):
        # Тест невалидного email при создании
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="password123"
            )
    
    def test_user_create_short_password(self):
        # Тест слишком короткого пароля
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="12345" 
            )
    
    def test_user_out_serialization(self, test_user):
        # Тест сериализации UserOut
        user_out = UserOut.model_validate(test_user)
        
        assert user_out.id == test_user.id
        assert user_out.email == test_user.email
        assert user_out.is_verified == test_user.is_verified
    
    def test_token_schema(self):
        # Тест схемы токена
        token = Token(
            access_token="access_123",
            refresh_token="refresh_456",
            token_type="bearer"
        )
        
        assert token.access_token == "access_123"
        assert token.refresh_token == "refresh_456"
        assert token.token_type == "bearer"
    
    def test_email_verification_schema(self):
        # Тест схемы верификации email
        verification = EmailVerification(token="verify_token_123")
        
        assert verification.token == "verify_token_123"
    
    def test_password_reset_request_schema(self):
        # Тест схемы запроса сброса пароля
        request = PasswordResetRequest(email="test@example.com")
        
        assert request.email == "test@example.com"
    
    def test_password_reset_schema(self):
        # Тест схемы сброса пароля
        reset = PasswordReset(
            token="reset_token",
            new_password="newpass123"
        )
        
        assert reset.token == "reset_token"
        assert reset.new_password == "newpass123"
    
    def test_password_reset_short_password(self):
        # Тест сброса с коротким паролем
        with pytest.raises(ValidationError):
            PasswordReset(
                token="reset_token",
                new_password="12345" 
            )
    
    def test_message_schema(self):
        # Тест схемы сообщения
        message = Message(detail="Success message")
        assert message.detail == "Success message"


class TestDatabaseModels:
    
    def test_user_model_creation(self, db_session):
        # Тест создания модели User
        from models import User
        from auth.jwt_utils import get_password_hash
        
        user = User(
            email="newuser@example.com",
            hashed_password=get_password_hash("pass"),
            is_verified=False
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_verified is False
        assert user.created_at is not None
    
    def test_user_model_relationships(self, test_user, test_contact):
        # Тест связей модели User
        assert len(test_user.contacts) == 1
        assert test_user.contacts[0].id == test_contact.id
    
    def test_contact_model_creation(self, db_session, test_user):
        # Тест создания модели Contact
        from models import Contacts
        
        contact = Contacts(
            name="Jane",
            surname="Smith",
            email="jane@example.com",
            phone="+380509999999",
            birthday=date(1995, 5, 15),
            extra="Colleague",
            user_id=test_user.id
        )
        
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)
        
        assert contact.id is not None
        assert contact.name == "Jane"
        assert contact.user_id == test_user.id
        assert contact.created_at is not None
    
    def test_contact_model_relationships(self, test_contact, test_user):
        # Тест связей модели Contact
        assert test_contact.owner.id == test_user.id
        assert test_contact.owner.email == test_user.email
    
    def test_cascade_delete(self, db_session, test_user, test_contact):
        # Тест каскадного удаления контактов при удалении пользователя
        contact_id = test_contact.id
        
        db_session.delete(test_user)
        db_session.commit()
        
        from models import Contacts
        deleted_contact = db_session.query(Contacts).filter(
            Contacts.id == contact_id
        ).first()
        assert deleted_contact is None


class TestDatabaseConnection:
    
    def test_get_db_session(self):
        # Тест получения сессии БД
        from database import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_database_tables_exist(self, db_session):
        # Тест существования таблиц в БД
        from sqlalchemy import inspect
        from database import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "users" in tables
        assert "contacts" in tables
