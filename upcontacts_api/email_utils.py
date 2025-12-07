import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Contact Book API"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

async def send_verification_email(email: str, token: str):
    # Отправка письма с подтверждением email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    verify_url = f"{frontend_url}/auth/verify-email?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Подтверждение email</h2>
            <p>Спасибо за регистрацию! Пожалуйста, подтвердите ваш email:</p>
            <a href="{verify_url}" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                Подтвердить email
            </a>
            <p>Или скопируйте ссылку: {verify_url}</p>
            <p>Токен действителен 24 часа.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Подтверждение email",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    await fm.send_message(message)

async def send_reset_password_email(email: str, token: str):
    # Отправка письма для сброса пароля
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    reset_url = f"{frontend_url}/auth/reset-password?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Сброс пароля</h2>
            <p>Вы запросили сброс пароля. Перейдите по ссылке:</p>
            <a href="{reset_url}" style="padding: 10px 20px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px;">
                Сбросить пароль
            </a>
            <p>Или скопируйте ссылку: {reset_url}</p>
            <p>Токен действителен 1 час.</p>
            <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Сброс пароля",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    await fm.send_message(message)