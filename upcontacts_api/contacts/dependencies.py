from fastapi import Depends
from auth.dependencies import get_current_user

def get_user_for_contact(current_user=Depends(get_current_user)):
    return current_user
