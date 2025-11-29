from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from auth.routes import router as auth_router
from contacts.routes import router as contacts_router, limiter
from database import engine, Base
from redis_client import test_redis_connection

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contact Book API",
    version="2.0.0",
    description="API with JWT auth, email verification, Redis caching, rate limiting, and Cloudinary avatars"
)

# Добавляем state для SlowAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - разрешаем все источники (настрой под свои нужды)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажи конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(contacts_router, prefix="/contacts", tags=["Contacts"])


@app.on_event("startup")
async def startup_event():
    """Проверка подключений при старте"""
    if test_redis_connection():
        print("✅ Redis connected successfully")
    else:
        print("❌ Redis connection failed")


@app.get("/")
def root():
    return {
        "message": "Contact Book API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    redis_status = test_redis_connection()
    return {
        "status": "ok",
        "redis": "connected" if redis_status else "disconnected"
    }


# Кастомная схема OpenAPI для Bearer токена
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите access_token из /auth/login"
        }
    }
    
    # Применяем security ко всем защищенным эндпоинтам
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                # Пропускаем публичные эндпоинты
                if path in ["/", "/health", "/auth/register", "/auth/login", 
                           "/auth/verify-email", "/auth/request-password-reset", 
                           "/auth/reset-password"]:
                    continue
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi