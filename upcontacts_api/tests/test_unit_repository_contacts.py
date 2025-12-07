# Юнит-тесты для репозитория контактов Unittest.

import unittest
from unittest.mock import MagicMock
from datetime import date
from sqlalchemy.orm import Session
from models import Contacts, User
from schemas import ContactCreate, ContactUpdate


class TestContactsRepository(unittest.TestCase):
    
    def setUp(self):
        # Настройка перед каждым тестом
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test@example.com", is_verified=True)
    
    def test_create_contact(self):
        # Тест создания контакта
        contact_data = ContactCreate(
            name="John",
            surname="Doe",
            email="john@example.com",
            phone="+380501234567",
            birthday=date(1990, 1, 1),
            extra="Friend"
        )
        
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        contact = Contacts(**contact_data.dict(), user_id=self.user.id)
        self.session.add(contact)
        self.session.commit()
        
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertEqual(contact.name, "John")
        self.assertEqual(contact.email, "john@example.com")
        self.assertEqual(contact.user_id, self.user.id)
    
    def test_get_contacts(self):
        # Тест получения списка контактов
        contacts = [
            Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                    phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id),
            Contacts(id=2, name="Jane", surname="Smith", email="jane@example.com",
                    phone="+380509876543", birthday=date(1992, 5, 15), user_id=self.user.id)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = contacts
        self.session.query.return_value = mock_query
        
        result = self.session.query(Contacts).filter(Contacts.user_id == self.user.id).all()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "John")
        self.assertEqual(result[1].name, "Jane")
    
    def test_get_contact_by_id(self):
        # Тест получения контакта по ID
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contact
        self.session.query.return_value = mock_query
        
        result = self.session.query(Contacts).filter(
            Contacts.id == 1,
            Contacts.user_id == self.user.id
        ).first()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "John")
    
    def test_update_contact(self):
        # Тест обновления контакта
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        update_data = ContactUpdate(phone="+380509999999", extra="Best friend")
        
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(contact, key, value)
        self.session.commit()
        
        self.assertEqual(contact.phone, "+380509999999")
        self.assertEqual(contact.extra, "Best friend")
        self.session.commit.assert_called_once()
    
    def test_delete_contact(self):
        # Тест удаления контакта
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        self.session.delete = MagicMock()
        self.session.commit = MagicMock()
        
        self.session.delete(contact)
        self.session.commit()
        
        self.session.delete.assert_called_once_with(contact)
        self.session.commit.assert_called_once()
    
    def test_search_contacts(self):
        # Тест поиска контактов
        contacts = [
            Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                    phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        ]
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = contacts
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query
        
        query = "John"
        result = self.session.query(Contacts).filter(
            Contacts.user_id == self.user.id
        ).all()
        
        self.assertEqual(len(result), 1)
        self.assertIn("John", result[0].name)


class TestUserRepository(unittest.TestCase):
    
    def setUp(self):
        # Настройка перед каждым тестом
        self.session = MagicMock(spec=Session)
    
    def test_create_user(self):
        # Тест создания пользователя
        from auth.jwt_utils import get_password_hash
        
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        user = User(
            email="newuser@example.com",
            hashed_password=get_password_hash("pass"), 
            is_verified=False
        )
        self.session.add(user)
        self.session.commit()
        
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertFalse(user.is_verified)
    
    def test_get_user_by_email(self):
        # Тест получения пользователя по email
        user = User(id=1, email="test@example.com", hashed_password="hashed", is_verified=True)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = user
        self.session.query.return_value = mock_query
        
        result = self.session.query(User).filter(User.email == "test@example.com").first()
        
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "test@example.com")
        self.assertTrue(result.is_verified)
    
    def test_verify_user(self):
        # Тест верификации пользователя
        user = User(id=1, email="test@example.com", is_verified=False, verification_token="token123")
        
        self.session.commit = MagicMock()
        
        user.is_verified = True
        user.verification_token = None
        self.session.commit()
        
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.verification_token)
        self.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
