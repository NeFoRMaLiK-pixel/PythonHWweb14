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
    """Получить все контакты текущего пользователя"""
    return db.query(Contacts).filter(Contacts.user_id == current_user.id).all()


@router.get("/{contact_id}", response_model=ContactOut)
def read_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить конкретный контакт"""
    contact = db.query(Contacts).filter(
        Contacts.id == contact_id,
        Contacts.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Контакт не найден")
    return contact


@router.post("/", response_model=ContactOut, status_code=201)
@limiter.limit("10/minute")  # ОГРАНИЧЕНИЕ: 10 запросов в минуту
def create_contact(
    request: Request,
    contact: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новый контакт
    RATE LIMIT: 10 запросов в минуту на создание контактов
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
    """Обновить контакт"""
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
    """Удалить контакт"""
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
    """Поиск контактов по имени, фамилии или email"""
    contacts = db.query(Contacts).filter(
        Contacts.user_id == current_user.id,
        (
            Contacts.name.ilike(f"%{query}%") |
            Contacts.surname.ilike(f"%{query}%") |
            Contacts.email.ilike(f"%{query}%")
        )
    ).all()
    return contacts