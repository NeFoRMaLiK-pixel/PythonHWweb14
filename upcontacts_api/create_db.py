from database import engine, Base
from models import User, Contacts

Base.metadata.create_all(bind=engine)
print("База данных создана!")