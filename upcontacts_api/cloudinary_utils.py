import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Конфигурация Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_avatar(file_content: bytes, public_id: str) -> str:

    try:
        result = cloudinary.uploader.upload(
            file_content,
            folder="avatars",
            public_id=f"user_{public_id}",
            overwrite=True,
            transformation=[
                {"width": 250, "height": 250, "crop": "fill", "gravity": "face"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        return result.get("secure_url")
    except Exception as e:
        raise Exception(f"Ошибка загрузки в Cloudinary: {str(e)}")

def delete_avatar(public_id: str):
    # Удаляет аватар из Cloudinary
    try:
        cloudinary.uploader.destroy(f"avatars/user_{public_id}")
    except Exception as e:
        print(f"Ошибка удаления из Cloudinary: {str(e)}")