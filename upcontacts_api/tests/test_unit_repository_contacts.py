"""
Юнит-тесты для репозитория контактов (Unittest).
"""
import unittest
from unittest.mock import MagicMock
from datetime import date
from sqlalchemy.orm import Session
from models import Contacts, User
from schemas import ContactCreate, ContactUpdate


class TestContactsRepository(unittest.TestCase):
    """Тесты для операций с контактами."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, email="test@example.com", is_verified=True)
    
    def test_create_contact(self):
        """Тест создания контакта."""
        # Arrange
        contact_data = ContactCreate(
            name="John",
            surname="Doe",
            email="john@example.com",
            phone="+380501234567",
            birthday=date(1990, 1, 1),
            extra="Friend"
        )
        
        # Mock
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        # Act
        contact = Contacts(**contact_data.dict(), user_id=self.user.id)
        self.session.add(contact)
        self.session.commit()
        
        # Assert
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertEqual(contact.name, "John")
        self.assertEqual(contact.email, "john@example.com")
        self.assertEqual(contact.user_id, self.user.id)
    
    def test_get_contacts(self):
        """Тест получения списка контактов."""
        # Arrange
        contacts = [
            Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                    phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id),
            Contacts(id=2, name="Jane", surname="Smith", email="jane@example.com",
                    phone="+380509876543", birthday=date(1992, 5, 15), user_id=self.user.id)
        ]
        
        # Mock
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = contacts
        self.session.query.return_value = mock_query
        
        # Act
        result = self.session.query(Contacts).filter(Contacts.user_id == self.user.id).all()
        
        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "John")
        self.assertEqual(result[1].name, "Jane")
    
    def test_get_contact_by_id(self):
        """Тест получения контакта по ID."""
        # Arrange
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        # Mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = contact
        self.session.query.return_value = mock_query
        
        # Act
        result = self.session.query(Contacts).filter(
            Contacts.id == 1,
            Contacts.user_id == self.user.id
        ).first()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "John")
    
    def test_update_contact(self):
        """Тест обновления контакта."""
        # Arrange
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        update_data = ContactUpdate(phone="+380509999999", extra="Best friend")
        
        # Mock
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        # Act
        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(contact, key, value)
        self.session.commit()
        
        # Assert
        self.assertEqual(contact.phone, "+380509999999")
        self.assertEqual(contact.extra, "Best friend")
        self.session.commit.assert_called_once()
    
    def test_delete_contact(self):
        """Тест удаления контакта."""
        # Arrange
        contact = Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                          phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        
        # Mock
        self.session.delete = MagicMock()
        self.session.commit = MagicMock()
        
        # Act
        self.session.delete(contact)
        self.session.commit()
        
        # Assert
        self.session.delete.assert_called_once_with(contact)
        self.session.commit.assert_called_once()
    
    def test_search_contacts(self):
        """Тест поиска контактов."""
        # Arrange
        contacts = [
            Contacts(id=1, name="John", surname="Doe", email="john@example.com",
                    phone="+380501234567", birthday=date(1990, 1, 1), user_id=self.user.id)
        ]
        
        # Mock
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.all.return_value = contacts
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query
        
        # Act
        query = "John"
        result = self.session.query(Contacts).filter(
            Contacts.user_id == self.user.id
        ).all()
        
        # Assert
        self.assertEqual(len(result), 1)
        self.assertIn("John", result[0].name)


class TestUserRepository(unittest.TestCase):
    """Тесты для операций с пользователями."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.session = MagicMock(spec=Session)
    
    def test_create_user(self):
        """Тест создания пользователя."""
        # Arrange
        from auth.jwt_utils import get_password_hash
        
        # Mock
        self.session.add = MagicMock()
        self.session.commit = MagicMock()
        self.session.refresh = MagicMock()
        
        # Act
        user = User(
            email="newuser@example.com",
            hashed_password=get_password_hash("password123"),
            is_verified=False
        )
        self.session.add(user)
        self.session.commit()
        
        # Assert
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertFalse(user.is_verified)
    
    def test_get_user_by_email(self):
        """Тест получения пользователя по email."""
        # Arrange
        user = User(id=1, email="test@example.com", hashed_password="hashed", is_verified=True)
        
        # Mock
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = user
        self.session.query.return_value = mock_query
        
        # Act
        result = self.session.query(User).filter(User.email == "test@example.com").first()
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.email, "test@example.com")
        self.assertTrue(result.is_verified)
    
    def test_verify_user(self):
        """Тест верификации пользователя."""
        # Arrange
        user = User(id=1, email="test@example.com", is_verified=False, verification_token="token123")
        
        # Mock
        self.session.commit = MagicMock()
        
        # Act
        user.is_verified = True
        user.verification_token = None
        self.session.commit()
        
        # Assert
        self.assertTrue(user.is_verified)
        self.assertIsNone(user.verification_token)
        self.session.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()