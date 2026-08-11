import asyncio
import logging
import os
import shutil
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.media import router as media_router
from handlers.inline import router as inline_router
from utils.rate_limiter import RateLimitMiddleware
from utils.user_manager import UserRegisterMiddleware
from utils.subscription_middleware import SubscriptionMiddleware
from utils.history import init_db
from utils.backup import daily_backup_task


async def handle_ping(request):
    return web.Response(text="Bot is alive")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    print(f"✅ Web server started on port {port}")


def setup_cookies():
    """Render'ning read-only secret cookies faylini /tmp papkasiga o'tkazadi va debug ma'lumotlarini chiqaradi."""
    secret_path = "/etc/secrets/youtube_cookies.txt"
    target_cookie = "/tmp/youtube_cookies.txt"

    # 1. /etc/secrets/youtube_cookies.txt tekshirish
    if os.path.exists(secret_path):
        try:
            size = os.path.getsize(secret_path)
            msg = f"✅ Cookies fayl topildi: {size} bytes"
            print(msg)
            logging.info(msg)
        except Exception as e:
            msg = f"⚠️ Cookies fayli bor, lekin o'qib bo'lmadi: {e}"
            print(msg)
            logging.warning(msg)
    else:
        msg = f"❌ Cookies fayl topilmadi: {secret_path}"
        print(msg)
        logging.info(msg)

    # 2. /tmp/youtube_cookies.txt ga nusxalash
    secret_sources = [
        secret_path,
        "/etc/secrets/cookies.txt",
    ]
    if config.IG_COOKIES_PATH:
        secret_sources.insert(0, config.IG_COOKIES_PATH)

    copied = False
    for source in secret_sources:
        if os.path.exists(source):
            try:
                os.makedirs(os.path.dirname(target_cookie), exist_ok=True)
                shutil.copy2(source, target_cookie)
                msg = f"✅ Cookies /tmp ga nusxalandi ({source} -> {target_cookie})"
                print(msg)
                logging.info(msg)
                copied = True
                break
            except Exception as e:
                err_msg = f"❌ Cookies /tmp ga nusxalashda xatolik: {e}"
                print(err_msg)
                logging.error(err_msg)

    if not copied and not os.path.exists(target_cookie):
        msg = "⚠️ Birorta ham cookies manbasi topilmadi yoki /tmp ga nusxalanmadi."
        print(msg)
        logging.warning(msg)



async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    setup_cookies()

    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logging.error("Loyiha uchun BOT_TOKEN o'rnatilmagan! Iltimos, .env faylini tahrirlang.")
        sys.exit(1)

    init_db()
    asyncio.create_task(daily_backup_task())

    await start_web_server()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.outer_middleware(UserRegisterMiddleware())
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.message.outer_middleware(RateLimitMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())

    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(inline_router)
    dp.include_router(media_router)

    logging.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni qabul qilmoqda...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot faoliyati to'xtatildi.")

