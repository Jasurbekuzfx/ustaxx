import json
import os
import config

def load_admins() -> list:
    """
    Admins.json faylidan adminlar ID ro'yxatini yuklaydi.
    """
    if not os.path.exists(config.ADMINS_FILE):
        return []
    try:
        with open(config.ADMINS_FILE, "r") as f:
            data = json.load(f)
            return list(data) if isinstance(data, list) else []
    except Exception as e:
        print(f"Admin ro'yxatini o'qishda xatolik: {e}")
        return []

def save_admins(admins: list):
    """
    Adminlar ro'yxatini faylga yozadi.
    """
    try:
        with open(config.ADMINS_FILE, "w") as f:
            json.dump(admins, f, indent=4)
    except Exception as e:
        print(f"Admin ro'yxatini saqlashda xatolik: {e}")

def is_super_admin(user_id: int) -> bool:
    """
    Foydalanuvchi Super Admin ekanligini tekshiradi (.env dagi ID bilan).
    """
    return user_id == config.SUPER_ADMIN_ID

def is_admin(user_id: int) -> bool:
    """
    Foydalanuvchi oddiy admin yoki super admin ekanligini tekshiradi.
    """
    if is_super_admin(user_id):
        return True
    admins = load_admins()
    return user_id in admins

def add_admin(user_id: int) -> bool:
    """
    Yangi admin qo'shadi. Agar allaqachon admin bo'lsa False qaytaradi.
    """
    admins = load_admins()
    if user_id in admins or is_super_admin(user_id):
        return False
    admins.append(user_id)
    save_admins(admins)
    return True

def remove_admin(user_id: int) -> bool:
    """
    Adminni o'chiradi. Agar ro'yxatda bo'lmasa False qaytaradi.
    """
    admins = load_admins()
    if user_id not in admins:
        return False
    admins.remove(user_id)
    save_admins(admins)
    return True

def get_admins() -> list:
    """
    Barcha oddiy adminlar ID ro'yxatini qaytaradi.
    """
    return load_admins()
