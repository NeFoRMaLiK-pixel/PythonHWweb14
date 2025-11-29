import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import (
    UserCreate, UserOut, Token, Message,
    EmailVerification, PasswordResetRequest, PasswordReset
)
from auth.jwt_handler import create_access_token, create_refresh_token
from auth.jwt_utils import verify_password, get_password_hash
from auth.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from email_utils import send_verification_email, send_reset_password_email
from redis_client import cache_user, delete_cached_user
from cloudinary_utils import upload_avatar

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя с отправкой письма верификации"""
    user = db.query(User).filter(User.email == user_create.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    # Создаем токен верификации
    verification_token = secrets.token_urlsafe(32)
    
    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        email=user_create.email,
        hashed_password=hashed_password,
        is_verified=False,
        verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Отправляем письмо верификации
    await send_verification_email(new_user.email, verification_token)
    
    return new_user

@router.get("/verify-email", response_model=Message)
def verify_email(token: str, db: Session = Depends(get_db)):
    """Верификация email по токену"""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший токен верификации"
        )
    
    if user.is_verified:
        return {"detail": "Email уже подтвержден"}
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"detail": "Email успешно подтвержден"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Логин пользователя"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email не подтвержден. Проверьте почту."
        )

    # Кэшируем пользователя при входе
    cache_user(user.email, {
        "id": user.id,
        "email": user.email,
        "is_verified": user.is_verified,
        "avatar_url": user.avatar_url
    })

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/request-password-reset", response_model=Message)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Запрос на сброс пароля"""
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        # Не раскрываем, существует ли пользователь
        return {"detail": "Если email существует, письмо отправлено"}
    
    # Создаем токен сброса пароля
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Отправляем письмо
    await send_reset_password_email(user.email, reset_token)
    
    return {"detail": "Если email существует, письмо отправлено"}

@router.post("/reset-password", response_model=Message)
def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Сброс пароля по токену"""
    user = db.query(User).filter(User.reset_token == reset_data.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или истекший токен"
        )
    
    # Проверяем срок действия токена
    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Токен истек"
        )
    
    # Обновляем пароль
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    # Удаляем кэш пользователя
    delete_cached_user(user.email)
    
    return {"detail": "Пароль успешно изменен"}

@router.post("/upload-avatar", response_model=UserOut)
async def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загрузка аватара пользователя в Cloudinary"""
    # Проверка типа файла
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только изображения: JPEG, PNG"
        )
    
    # Проверка размера (макс 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Размер файла не должен превышать 5MB"
        )
    
    try:
        # Загружаем в Cloudinary
        avatar_url = upload_avatar(contents, str(current_user.id))
        
        # Обновляем в БД
        current_user.avatar_url = avatar_url
        db.commit()
        db.refresh(current_user)
        
        # Обновляем кэш
        delete_cached_user(current_user.email)
        cache_user(current_user.email, {
            "id": current_user.id,
            "email": current_user.email,
            "is_verified": current_user.is_verified,
            "avatar_url": avatar_url
        })
        
        return current_user
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки аватара: {str(e)}"
        )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user