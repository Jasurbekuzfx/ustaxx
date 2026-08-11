from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware, Bot, html
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    Message, TelegramObject,
)

from utils.admin_manager import is_admin
from utils.channel_manager import load_channels


async def check_user_subscription(bot: Bot, user_id: int) -> tuple[bool, List[dict]]:
    channels = load_channels()
    if not channels:
        return True, []

    not_subscribed = []
    for ch in channels:
        channel_id = ch["id"]
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception:
            not_subscribed.append(ch)

    return len(not_subscribed) == 0, not_subscribed


def build_subscription_keyboard(channels: List[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        cid = ch["id"]
        title = ch.get("title", cid)
        link = cid if cid.startswith("http") else f"https://t.me/{cid.lstrip('@')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {title}", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


SUBSCRIPTION_TEXT = (
    "⚠️ "
    + html.bold("Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:")
    + "\n\n"
    + "Obuna bo'lganingizdan so'ng \"✅ Tekshirish\" tugmasini bosing."
)

MEDIA_CALLBACK_PREFIXES = ("quality:", "redl:", "dl_song:", "get_audio:", "prof:")


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        bot: Bot = data.get("bot")

        if isinstance(event, Message):
            if not event.from_user:
                return await handler(event, data)
            user_id = event.from_user.id
            bot = bot or event.bot

            if is_admin(user_id):
                return await handler(event, data)

            if event.text and event.text.startswith("/"):
                cmd = event.text.split()[0].lower()
                allowed = (
                    "/start", "/help", "/history",
                    "/admin", "/stats", "/broadcast", "/addadmin", "/removeadmin",
                    "/admins", "/addchannel", "/removechannel", "/channels",
                )
                if cmd in allowed:
                    return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            if not event.from_user:
                return await handler(event, data)
            user_id = event.from_user.id
            bot = bot or event.bot

            if is_admin(user_id):
                return await handler(event, data)

            if event.data == "check_sub" or event.data.startswith("admin_"):
                return await handler(event, data)

            if not event.data or not any(event.data.startswith(p) for p in MEDIA_CALLBACK_PREFIXES):
                return await handler(event, data)
        else:
            return await handler(event, data)

        channels = load_channels()
        if not channels:
            return await handler(event, data)

        subscribed, not_sub = await check_user_subscription(bot, user_id)
        if subscribed:
            return await handler(event, data)

        if isinstance(event, Message):
            await event.answer(SUBSCRIPTION_TEXT, reply_markup=build_subscription_keyboard(not_sub))
        elif isinstance(event, CallbackQuery):
            await event.answer("❌ Avval kanallarga obuna bo'ling!", show_alert=True)
            try:
                await event.message.answer(SUBSCRIPTION_TEXT, reply_markup=build_subscription_keyboard(not_sub))
            except Exception:
                pass
        return None
