"""
Маршруты для работы с контактами.

Этот модуль содержит все эндпоинты для CRUD операций с контактами,
включая создание, чтение, обновление, удаление и поиск.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Contacts, User
from schemas import ContactCreate, ContactUpdate, ContactOut
from typing import List
from auth.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

# Инициализация rate limiter
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.get("/", response_model=List[ContactOut])
def read_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить все контакты текущего пользователя.
    
    Args:
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        List[ContactOut]: Список всех контактов пользователя
    """
    return db.query(Contacts).filter(Contacts.user_id == current_user.id).all()


@router.get("/{contact_id}", response_model=ContactOut)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получить конкретный контакт по ID.
    
    Args:
        contact_id (int): Уникальный идентификатор контакта
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        ContactOut: Данные запрошенного контакта
        
    Raises:
        HTTPException: 404 если контакт не найден или не принадлежит пользователю
    """
    contact = db.query(Contacts).filter(
        Contacts.id == contact_id,
        Contacts.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return contact


@router.post("/", response_model=ContactOut, status_code=201)
@limiter.limit("10/minute")
def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новый контакт.
    
    **Rate Limit:** 10 запросов в минуту на создание контактов.
    
    **Требования:**
    - Аутентификация: Bearer токен обязателен
    - Email контакта должен быть уникальным для данного пользователя
    - Телефон должен соответствовать формату: +[код][номер]
    
    Args:
        request (Request): HTTP запрос (для rate limiting)
        contact (ContactCreate): Данные нового контакта (имя, фамилия, email, телефон, дата рождения)
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        ContactOut: Созданный контакт с присвоенным ID
        
    Raises:
        HTTPException: 
            - 400 если контакт с таким email уже существует у пользователя
            - 422 если данные не прошли валидацию
            - 429 если превышен лимит запросов (более 10 в минуту)
    """
    # Проверка на дубликат email в контактах этого пользователя
    existing = db.query(Contacts).filter(
        Contacts.email == contact.email,
        Contacts.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Контакт с таким email уже существует"
        )
    
    db_contact = Contacts(**contact.dict(), user_id=current_user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.put("/{contact_id}", response_model=ContactOut)
def update_contact(
    contact_id: int,
    contact_update: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить существующий контакт.
    
    Позволяет частичное обновление - можно изменить только некоторые поля.
    
    Args:
        contact_id (int): ID контакта для обновления
        contact_update (ContactUpdate): Данные для обновления (все поля опциональны)
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        ContactOut: Обновленный контакт
        
    Raises:
        HTTPException: 
            - 404 если контакт не найден или не принадлежит пользователю
            - 400 если новый email уже используется другим контактом пользователя
    """
    contact = db.query(Contacts).filter(
        Contacts.id == contact_id,
        Contacts.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")

    # Проверка на дубликат email при обновлении
    if contact_update.email:
        existing = db.query(Contacts).filter(
            Contacts.email == contact_update.email,
            Contacts.user_id == current_user.id,
            Contacts.id != contact_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Контакт с таким email уже существует"
            )

    for key, value in contact_update.dict(exclude_unset=True).items():
        setattr(contact, key, value)
    
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить контакт.
    
    Args:
        contact_id (int): ID контакта для удаления
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        dict: Сообщение об успешном удалении
        
    Raises:
        HTTPException: 404 если контакт не найден или не принадлежит пользователю
    """
    contact = db.query(Contacts).filter(
        Contacts.id == contact_id,
        Contacts.user_id == current_user.id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    
    db.delete(contact)
    db.commit()
    return {"detail": "Контакт удалён"}


@router.get("/search/", response_model=List[ContactOut])
def search_contacts(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Поиск контактов по имени, фамилии или email.
    
    Выполняет регистронезависимый поиск по подстроке во всех трех полях.
    
    Args:
        query (str): Поисковый запрос (минимум 1 символ)
        db (Session): Сессия базы данных
        current_user (User): Текущий авторизованный пользователь
        
    Returns:
        List[ContactOut]: Список контактов, соответствующих запросу
        
    Example:
        GET /contacts/search/?query=John
        Вернет всех контактов где имя, фамилия или email содержит "John"
    """
    contacts = db.query(Contacts).filter(
        Contacts.user_id == current_user.id,
        (
            Contacts.name.ilike(f"%{query}%") |
            Contacts.surname.ilike(f"%{query}%") |
            Contacts.email.ilike(f"%{query}%")
        )
    ).all()
    return contacts