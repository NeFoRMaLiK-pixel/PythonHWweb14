from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

# Контакты
class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    surname: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')
    birthday: date
    extra: Optional[str] = Field(None, max_length=255)

class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    surname: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[0-9]{10,15}$')
    birthday: Optional[date] = None
    extra: Optional[str] = Field(None, max_length=255)

class ContactOut(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr
    phone: str
    birthday: date
    extra: Optional[str] = None

    class Config:
        from_attributes = True

# Пользователи
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

# Схема для логина
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Схема для токена
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

# Схемы для верификации и сброса пароля
class EmailVerification(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# Схема сообщения
class Message(BaseModel):
    detail: str