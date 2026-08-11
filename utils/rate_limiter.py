import time
from typing import Callable, Dict, Any, Awaitable, List
from aiogram import BaseMiddleware
from aiogram.types import Message
import config

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = None, window: int = None):
        self.limit = limit if limit is not None else config.RATE_LIMIT_LIMIT
        self.window = window if window is not None else config.RATE_LIMIT_WINDOW
        # Key: user_id (int), Value: list of timestamps (float)
        self.users: Dict[int, List[float]] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Faqat foydalanuvchidan kelgan xabarlarga ishlov beramiz
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = time.time()

        if user_id not in self.users:
            self.users[user_id] = []

        # Window vaqtidan eski so'rovlarni o'chiramiz
        self.users[user_id] = [t for t in self.users[user_id] if current_time - t < self.window]

        # Cheklovdan oshib ketganini tekshirish
        if len(self.users[user_id]) >= self.limit:
            # Agar rate limit buzilgan bo'lsa, foydalanuvchiga ogohlantirish beramiz
            # Bu yerda har bir ortiqcha xabarga javob bermaslik uchun oxirgi javob vaqtini ham tekshirsa bo'ladi,
            # lekin soddalik uchun to'g'ridan-to'g'ri ogohlantirish qaytaramiz.
            await event.answer(
                f"⚠️ Juda ko'p so'rov yubordingiz.\n"
                f"Sizga daqiqasiga {self.limit} ta so'rov ruxsat etilgan. "
                f"Iltimos, biroz kuting."
            )
            return

        # Yangi so'rov vaqtini qo'shamiz va handler'ni davom ettiramiz
        self.users[user_id].append(current_time)
        return await handler(event, data)
