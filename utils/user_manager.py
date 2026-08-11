import json
import os
import config

def load_users() -> list:
    """
    Users.json faylidan foydalanuvchilar ID ro'yxatini yuklaydi.
    """
    if not os.path.exists(config.USERS_FILE):
        return []
    try:
        with open(config.USERS_FILE, "r") as f:
            data = json.load(f)
            return list(data) if isinstance(data, list) else []
    except Exception as e:
        print(f"Foydalanuvchilar ro'yxatini o'qishda xatolik: {e}")
        return []

def save_users(users: list):
    """
    Foydalanuvchilar ro'yxatini faylga yozadi.
    """
    try:
        with open(config.USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        print(f"Foydalanuvchilar ro'yxatini saqlashda xatolik: {e}")

def add_user(user_id: int) -> bool:
    """
    Yangi foydalanuvchini ro'yxatga oladi. Agar allaqachon mavjud bo'lsa False qaytaradi.
    """
    users = load_users()
    if user_id in users:
        return False
    users.append(user_id)
    save_users(users)
    return True

def get_users_count() -> int:
    """
    Jami ro'yxatdan o'tgan foydalanuvchilar sonini qaytaradi.
    """
    return len(load_users())

def get_all_users() -> list:
    """
    Barcha foydalanuvchilar ID ro'yxatini qaytaradi.
    """
    return load_users()

# Middleware user registration uchun
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

class UserRegisterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            # Foydalanuvchini bazaga qo'shish
            add_user(event.from_user.id)
        return await handler(event, data)

