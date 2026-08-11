from datetime import datetime
from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from utils.history import get_user_history
from utils.platforms import PLATFORM_LABELS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.full_name if message.from_user else "Foydalanuvchi"
    welcome_text = (
        f"Assalomu alaykum, {html.bold(user_name)}!\n\n"
        f"🤖 Ushbu bot yordamida quyidagilarni qilishingiz mumkin:\n\n"
        f"📸 {html.bold('Instagram')} — Reels, Post va Karusel\n"
        f"🎵 {html.bold('TikTok')} — Suv belgisiz video va audio\n"
        f"📘 {html.bold('Facebook')} — Reels va videolar\n"
        f"📌 {html.bold('Pinterest')} — Video va rasmlar\n"
        f"👻 {html.bold('Snapchat')} • ❤️ {html.bold('Likee')} • 🧵 {html.bold('Threads')}\n"
        f"▶️ {html.bold('YouTube Shorts')}\n"
        f"🔍 {html.bold('Shazam')} — Qo'shiqni aniqlash\n\n"
        f"💡 Havolani yuboring, sifat tanlang va yuklab oling.\n"
        f"Yordam: /help • Tarix: /history"
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        f"ℹ️ {html.bold('Botdan foydalanish boʻyicha yoʻriqnoma:')}\n\n"
        f"1️⃣ {html.bold('Media yuklab olish:')}\n"
        f"Instagram, TikTok, Facebook, Pinterest, Snapchat, Likee, Threads "
        f"yoki YouTube Shorts havolasini yuboring. Sifat tanlang (720p / 1080p / Audio).\n\n"
        f"2️⃣ {html.bold('Qoʻshiq qidirish:')}\n"
        f"Qo'shiq nomini yozing yoki inline rejimda: {html.code('@bot_username qoshiq nomi')}\n\n"
        f"3️⃣ {html.bold('Shazam:')}\n"
        f"Voice, audio yoki video yuboring — bot qo'shiqni aniqlaydi.\n\n"
        f"4️⃣ {html.bold('Tarix:')}\n"
        f"/history — oxirgi 20 ta yuklab olishingizni ko'ring."
    )
    await message.answer(help_text)


@router.message(Command("history"))
async def cmd_history(message: Message):
    records = get_user_history(message.from_user.id, limit=20)
    if not records:
        await message.answer("📭 Sizda hali yuklab olish tarixi yo'q.")
        return

    text = f"📜 {html.bold('Yuklab olish tarixingiz')} (oxirgi 20 ta):\n\n"
    buttons = []

    for idx, rec in enumerate(records, 1):
        platform_label = PLATFORM_LABELS.get(rec["platform"], rec["platform"])
        try:
            dt = datetime.fromisoformat(rec["created_at"])
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            date_str = rec["created_at"][:16]
        title_short = rec["title"][:40] + ("..." if len(rec["title"]) > 40 else "")
        text += f"{idx}. [{date_str}] {platform_label} — {html.quote(title_short)}\n"
        buttons.append([
            InlineKeyboardButton(
                text=f"🔄 {idx}. Qayta yuklash",
                callback_data=f"redl:{rec['id']}",
            )
        ])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
