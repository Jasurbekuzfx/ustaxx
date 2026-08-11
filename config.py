import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN")
IG_COOKIES_PATH = os.getenv("IG_COOKIES_PATH")

# Rate limit sozlamalari (default: 5 so'rov / 60 sekund)
try:
    RATE_LIMIT_LIMIT = int(os.getenv("RATE_LIMIT_LIMIT", "5"))
except ValueError:
    RATE_LIMIT_LIMIT = 5

try:
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
except ValueError:
    RATE_LIMIT_WINDOW = 60

# Vaqtincha fayllar uchun temp papkasi
# Agarda operatsion tizim Linux bo'lsa /tmp ishlatiladi, aks holda tempfile.gettempdir()
import tempfile
TEMP_DIR = Path("/tmp") if os.name != "nt" else Path(tempfile.gettempdir())

# Agar TEMP_DIR mavjud bo'lmasa uni yaratish
TEMP_DIR.mkdir(parents=True, exist_ok=True)

if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("⚠️ DIQQAT: BOT_TOKEN o'rnatilmagan yoki noto'g'ri. Iltimos, .env faylini to'ldiring!")

# Super admin ID (.env dan o'qiladi)
try:
    SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))
except ValueError:
    SUPER_ADMIN_ID = 0

# Ma'lumotlarni saqlash fayllari
ADMINS_FILE = BASE_DIR / "admins.json"
USERS_FILE = BASE_DIR / "users.json"
CHANNELS_FILE = BASE_DIR / "channels.json"
HISTORY_DB = BASE_DIR / "history.db"

