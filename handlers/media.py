import asyncio
import os
import re
import uuid
import shutil
from aiogram import Router, F, html
from aiogram.types import (
    Message, CallbackQuery, FSInputFile, InputMediaPhoto, InputMediaVideo,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from utils.downloader import universal_download, download_profile, cleanup_directory, VIDEO_EXTENSIONS
from utils.shazam_util import identify_audio, extract_audio_from_video
from utils.platforms import analyze_url, PLATFORM_LABELS
from utils.music_search import SEARCH_CACHE, search_youtube_flat, download_yt_audio_sync, auto_cleanup_search_cache
from utils.url_cache import store_url, get_cached_url
from utils.history import record_download, get_user_history, get_download_by_id
from utils.subscription_middleware import (
    check_user_subscription, build_subscription_keyboard, SUBSCRIPTION_TEXT,
)
import config

router = Router()

DOWNLOADS_DIR = os.path.join(config.TEMP_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

VIDEO_TITLES = {}


def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def save_temp_video(user_id: int, unique_id: str, source_path: str, title: str) -> str:
    dest_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_{unique_id}.mp4")
    shutil.copy2(source_path, dest_path)
    VIDEO_TITLES[unique_id] = title
    asyncio.create_task(auto_delete_video(user_id, unique_id))
    return dest_path


async def auto_delete_video(user_id: int, unique_id: str, delay: int = 600):
    await asyncio.sleep(delay)
    file_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_{unique_id}.mp4")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    VIDEO_TITLES.pop(unique_id, None)


def build_quality_keyboard(url_hash: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔹 720p", callback_data=f"quality:720:{url_hash}"),
            InlineKeyboardButton(text="🔹 1080p", callback_data=f"quality:1080:{url_hash}"),
        ],
        [
            InlineKeyboardButton(text="🎵 Faqat audio", callback_data=f"quality:audio:{url_hash}"),
        ],
    ])


def build_profile_limit_keyboard(url_hash: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖼 3 ta oxirgi", callback_data=f"prof:3:{url_hash}"),
            InlineKeyboardButton(text="🖼 5 ta oxirgi", callback_data=f"prof:5:{url_hash}"),
            InlineKeyboardButton(text="🖼 10 ta oxirgi", callback_data=f"prof:10:{url_hash}"),
        ],
    ])


async def send_download_result(message: Message, result, url: str, platform: str):
    """Yuklab olingan natijani Telegram'ga yuboradi va tarixga yozadi."""
    temp_dir = None
    if result.file_paths:
        temp_dir = os.path.dirname(result.file_paths[0])
    elif result.audio_path:
        temp_dir = os.path.dirname(result.audio_path)

    try:
        user_id = message.from_user.id

        if len(result.file_paths) > 1:
            chunks = list(chunk_list(result.file_paths, 10))
            first_video_path = None
            for chunk_idx, chunk in enumerate(chunks):
                media_group = []
                for i, path in enumerate(chunk):
                    is_video = path.lower().endswith(VIDEO_EXTENSIONS)
                    if is_video and not first_video_path:
                        first_video_path = path
                    caption = result.title[:1024] if chunk_idx == 0 and i == 0 else None
                    if is_video:
                        media_group.append(InputMediaVideo(media=FSInputFile(path), caption=caption))
                    else:
                        media_group.append(InputMediaPhoto(media=FSInputFile(path), caption=caption))
                await message.answer_media_group(media=media_group)
            if first_video_path:
                uid = str(uuid.uuid4())[:8]
                save_temp_video(user_id, uid, first_video_path, result.title)
                await message.answer(
                    "🎵 Musiqasini yuklab olish uchun tugmani bosing:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎵 Qo'shiqni yuklab olish", callback_data=f"get_audio:{uid}")]
                    ]),
                )

        elif len(result.file_paths) == 1:
            file_path = result.file_paths[0]
            is_video = file_path.lower().endswith(VIDEO_EXTENSIONS)
            caption = result.title[:1024] if result.title else None
            if is_video:
                uid = str(uuid.uuid4())[:8]
                save_temp_video(user_id, uid, file_path, result.title)
                await message.answer_video(
                    FSInputFile(file_path), caption=caption,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🎵 Qo'shiqni yuklab olish", callback_data=f"get_audio:{uid}")]
                    ]),
                )
            else:
                await message.answer_photo(FSInputFile(file_path), caption=caption)

        elif result.audio_path and os.path.exists(result.audio_path):
            caption = f"🎵 {result.title[:200]} (Audio)" if result.title else "🎵 Audio"
            await message.answer_audio(FSInputFile(result.audio_path), caption=caption)

        if result.success:
            record_download(user_id, platform, result.title or url, url)

    except Exception as e:
        await message.answer(f"❌ Telegramga yuborishda xatolik yuz berdi: {str(e)}")
    finally:
        if temp_dir:
            cleanup_directory(temp_dir)


async def process_download(message: Message, url: str, platform: str, quality: str = "1080"):
    loading_msg = await message.answer("⏳ Yuklanmoqda...")
    result = await universal_download(url, platform, quality)

    if not result.success:
        await loading_msg.edit_text(
            f"❌ Yuklab olishda xatolik yuz berdi:\n{html.code(result.error or 'Noma`lum xatolik')}"
        )
        return

    await loading_msg.edit_text("📤 Telegram'ga yuklanmoqda...")
    await send_download_result(message, result, url, platform)
    try:
        await loading_msg.delete()
    except Exception:
        pass


@router.message(F.text)
async def handle_text(message: Message):
    text = message.text.strip()
    detected = analyze_url(text)

    if detected:
        platform, kind, url, username = detected
        url_hash = store_url(url, platform, message.from_user.id, kind=kind, username=username)
        label = PLATFORM_LABELS.get(platform, platform)
        if kind == "profile" and username:
            await message.answer(
                f"📥 {html.bold(label)} profil aniqlandi: {html.bold('@' + username)}\n"
                f"Yuklab olish sifati tanlang:",
                reply_markup=build_quality_keyboard(url_hash),
            )
        elif kind == "story":
            await message.answer(
                f"📥 {html.bold(label)} story aniqlandi.\n"
                f"Yuklab olish sifati tanlang:",
                reply_markup=build_quality_keyboard(url_hash),
            )
        else:
            await message.answer(
                f"📥 {html.bold(label)} havolasi aniqlandi.\n"
                f"Yuklab olish sifati tanlang:",
                reply_markup=build_quality_keyboard(url_hash),
            )
    elif text.startswith("/") or "http://" in text or "https://" in text:
        await message.answer(
            f"👋 Men quyidagi platformalardan yuklab olaman:\n\n"
            f"📸 Instagram • 🎵 TikTok • 📘 Facebook • 📌 Pinterest\n"
            f"👻 Snapchat • ❤️ Likee • 🧵 Threads • ▶️ YouTube\n\n"
            f"Shuningdek, qo'shiq nomini yozib qidirishingiz yoki audio/video yuborishingiz mumkin. 🎵"
        )
    else:
        await process_song_search(message, text)


@router.callback_query(F.data.startswith("quality:"))
async def handle_quality_callback(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("❌ Xatolik", show_alert=True)
        return

    quality, url_hash = parts[1], parts[2]
    cached = get_cached_url(url_hash)
    if not cached:
        await callback.answer("❌ Havola muddati tugagan, qayta yuboring.", show_alert=True)
        return

    if cached["user_id"] != callback.from_user.id:
        await callback.answer("❌ Bu havola sizga tegishli emas.", show_alert=True)
        return

    url, platform = cached["url"], cached["platform"]
    kind = cached.get("kind", "media")
    quality_label = {"720": "720p", "1080": "1080p", "audio": "Audio"}.get(quality, quality)
    await callback.answer(f"⏳ {quality_label} sifatda yuklanmoqda...")
    cached["quality"] = quality

    if kind == "profile":
        username = cached.get("username") or platform
        await callback.message.edit_text(
            f"🖼 Qancha oxirgi media yuklab olinadi?\n"
            f"👤 {html.bold('@' + username)}",
            reply_markup=build_profile_limit_keyboard(url_hash),
        )
        return

    await process_download(callback.message, url, platform, quality)


@router.callback_query(F.data.startswith("prof:"))
async def handle_profile_callback(callback: CallbackQuery):
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("❌ Xatolik", show_alert=True)
        return

    try:
        limit = int(parts[1])
    except ValueError:
        await callback.answer("❌ Xatolik", show_alert=True)
        return

    url_hash = parts[2]
    cached = get_cached_url(url_hash)
    if not cached:
        await callback.answer("❌ Havola muddati tugagan, qayta yuboring.", show_alert=True)
        return

    if cached["user_id"] != callback.from_user.id:
        await callback.answer("❌ Bu havola sizga tegishli emas.", show_alert=True)
        return

    quality = cached.get("quality", "1080")
    if quality == "audio":
        await callback.answer("⚠️ Profil uchun faqat video/rasm yuklanadi, 1080p ishlatiladi.", show_alert=True)
        quality = "1080"

    await callback.answer(f"⏳ {limit} ta media yuklanmoqda...")
    status_msg = await callback.message.answer(f"⏳ Profildan {limit} ta media yuklanmoqda...")
    result = await download_profile(cached["url"], cached["platform"], quality, limit)

    if not result.success:
        await status_msg.edit_text(
            f"❌ Profilni yuklab bo'lmadi:\n{html.code(result.error or 'Noma`lum xatolik')}"
        )
        return

    await status_msg.edit_text("📤 Telegram'ga yuklanmoqda...")
    username = cached.get("username")
    result.title = result.title or f"@{username or cached['platform']}"
    await send_download_result(callback.message, result, cached["url"], cached["platform"])
    try:
        await status_msg.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("redl:"))
async def handle_redownload(callback: CallbackQuery):
    record_id = callback.data.split(":", 1)[1]
    record = get_download_by_id(record_id, callback.from_user.id)
    if not record:
        await callback.answer("❌ Yozuv topilmadi.", show_alert=True)
        return

    url_hash = store_url(record["url"], record["platform"], callback.from_user.id)
    label = PLATFORM_LABELS.get(record["platform"], record["platform"])
    await callback.message.answer(
        f"🔄 {html.bold(html.quote(record['title']))} — sifat tanlang:",
        reply_markup=build_quality_keyboard(url_hash),
    )
    await callback.answer()


@router.callback_query(F.data == "check_sub")
async def handle_check_subscription(callback: CallbackQuery):
    subscribed, not_sub = await check_user_subscription(callback.bot, callback.from_user.id)
    if subscribed:
        await callback.message.edit_text("✅ Barcha kanallarga obuna bo'lgansiz! Endi botdan foydalanishingiz mumkin.")
        await callback.answer("✅ Obuna tasdiqlandi!")
    else:
        await callback.message.edit_text(
            SUBSCRIPTION_TEXT,
            reply_markup=build_subscription_keyboard(not_sub),
        )
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz.", show_alert=True)


async def process_song_search(message: Message, query: str):
    status_msg = await message.answer(f"🔍 {html.bold(html.quote(query))} bo'yicha qidirilmoqda...")
    try:
        loop = asyncio.get_event_loop()
        valid_results = await loop.run_in_executor(None, search_youtube_flat, query, 10)
        if not valid_results:
            await status_msg.edit_text("❌ Bunday qo'shiq topilmadi")
            return

        search_id = str(uuid.uuid4())[:8]
        SEARCH_CACHE[search_id] = {i + 1: item for i, item in enumerate(valid_results)}
        asyncio.create_task(auto_cleanup_search_cache(search_id))

        response_text = f"🔍 \"{html.bold(html.quote(query))}\" bo'yicha natijalar:\n\n"
        for idx, item in enumerate(valid_results, 1):
            artist = item.get("artist")
            artist_part = f" — {html.quote(artist)}" if artist else ""
            response_text += f"{idx}. {html.quote(item['title'])}{artist_part} — {item['duration_str']}\n"

        buttons = []
        row = []
        for idx in range(1, len(valid_results) + 1):
            row.append(InlineKeyboardButton(text=str(idx), callback_data=f"dl_song:{search_id}:{idx}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        await status_msg.edit_text(response_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        await status_msg.edit_text(f"❌ Qidirishda xatolik yuz berdi: {str(e)}")


@router.callback_query(F.data.startswith("dl_song:"))
async def handle_dl_song_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)
        return
    search_id = parts[1]
    try:
        idx = int(parts[2])
    except ValueError:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)
        return
    song_info = SEARCH_CACHE.get(search_id, {}).get(idx)
    if not song_info:
        await callback.answer("❌ Qidiruv seansining vaqti tugagan.", show_alert=True)
        return

    await callback.answer(f"⏳ {idx}-natija yuklab olinmoqda...")
    title = song_info["title"]
    status_msg = await callback.message.answer(f"📥 {html.bold(html.quote(title))} yuklanmoqda...")
    temp_dir = None
    try:
        loop = asyncio.get_event_loop()
        temp_dir, audio_path = await loop.run_in_executor(None, download_yt_audio_sync, song_info["video_id"])
        if audio_path and os.path.exists(audio_path):
            safe = re.sub(r'[^\w\s-]', '', title[:50]).strip() or "song"
            await callback.message.answer_audio(
                FSInputFile(audio_path, filename=f"{safe}.mp3"),
                caption=f"🎵 {title[:200]}",
            )
        else:
            await callback.message.answer("❌ Qo'shiqni yuklab bo'lmadi.")
    except Exception as e:
        await callback.message.answer(f"❌ Audio yuklashda xatolik: {str(e)}")
    finally:
        if temp_dir:
            cleanup_directory(temp_dir)
        try:
            await status_msg.delete()
        except Exception:
            pass


@router.callback_query(F.data.startswith("get_audio:"))
async def handle_get_audio_callback(callback: CallbackQuery):
    unique_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    video_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_{unique_id}.mp4")
    if not os.path.exists(video_path):
        await callback.answer("❌ Fayl muddati tugagan, videoni qayta yuboring", show_alert=True)
        return

    await callback.answer("⏳ Audio ajratilmoqda...")
    audio_path = os.path.join(DOWNLOADS_DIR, f"{user_id}_{unique_id}.mp3")
    try:
        success = await extract_audio_from_video(video_path, audio_path)
        if success and os.path.exists(audio_path):
            title = VIDEO_TITLES.get(unique_id, "Audio")
            safe = re.sub(r'[^\w\s-]', '', title[:50]).strip() or "audio"
            await callback.message.answer_audio(
                FSInputFile(audio_path, filename=f"{safe}.mp3"),
                caption=f"🎵 {title[:200]}" if title else "🎵 Audio",
            )
        else:
            await callback.message.answer("❌ Videodan audioni ajratib bo'lmadi.")
    except Exception as e:
        await callback.message.answer(f"❌ Audio ajratishda xatolik: {str(e)}")
    finally:
        for p in (video_path, audio_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        VIDEO_TITLES.pop(unique_id, None)


@router.message(F.voice | F.audio | F.video | F.video_note | (F.document & F.document.mime_type.startswith(("audio/", "video/"))))
async def handle_shazam_media(message: Message):
    file_id = file_size = None
    file_ext = ".mp3"

    if message.voice:
        file_id, file_size, file_ext = message.voice.file_id, message.voice.file_size, ".ogg"
    elif message.audio:
        file_id = message.audio.file_id
        file_size = message.audio.file_size
        file_ext = os.path.splitext(message.audio.file_name or "audio.mp3")[1]
    elif message.video:
        file_id, file_size, file_ext = message.video.file_id, message.video.file_size, ".mp4"
    elif message.video_note:
        file_id, file_size, file_ext = message.video_note.file_id, message.video_note.file_size, ".mp4"
    elif message.document:
        file_id = message.document.file_id
        file_size = message.document.file_size
        file_ext = os.path.splitext(message.document.file_name or "file.mp3")[1]

    if file_size and file_size > 20 * 1024 * 1024:
        await message.answer("⚠️ 20MB dan katta fayllarni qayta ishlay olmayman.")
        return

    unique_id = str(uuid.uuid4())
    temp_dir = os.path.join(config.TEMP_DIR, unique_id)
    os.makedirs(temp_dir, exist_ok=True)
    download_path = os.path.join(temp_dir, f"input{file_ext}")
    shazam_input = download_path
    status_msg = await message.answer("🔍 Qo'shiq izlanmoqda...")

    try:
        file_info = await message.bot.get_file(file_id)
        await message.bot.download_file(file_info.file_path, download_path)

        if file_ext.lower() in (".mp4", ".mkv", ".mov", ".avi", ".webm", ".3gp"):
            await status_msg.edit_text("🎵 Videodan audio ajratib olinmoqda...")
            extracted = os.path.join(temp_dir, "extracted.mp3")
            if await extract_audio_from_video(download_path, extracted):
                shazam_input = extracted
            else:
                await status_msg.edit_text("❌ Videodan audioni ajratib bo'lmadi.")
                return

        await status_msg.edit_text("🔍 Shazam orqali qidirilmoqda...")
        result = await identify_audio(shazam_input)
        if result:
            text = (
                f"🎵 {html.bold('Qoʻshiq aniqlandi!')}\n\n"
                f"📝 {html.bold('Nomi:')} {result['title']}\n"
                f"👤 {html.bold('Ijrochi:')} {result['artist']}\n\n"
                f"🔗 {html.bold('Tinglash uchun havolalar:')}\n"
                f"• <a href='{result['spotify_url']}'>Spotify</a>\n"
                f"• <a href='{result['yt_music_url']}'>YouTube Music</a>\n"
            )
            if result.get('apple_music_url'):
                text += f"• <a href='{result['apple_music_url']}'>Apple Music</a>\n"
            if result.get('shazam_url'):
                text += f"• <a href='{result['shazam_url']}'>Shazam</a>\n"
            if result.get('coverart'):
                await message.answer_photo(photo=result['coverart'], caption=text)
            else:
                await message.answer(text)
        else:
            await message.answer("❌ Kechirasiz, bu qo'shiqni aniqlay olmadim")
    except Exception as e:
        await message.answer(f"❌ Musiqani aniqlashda xatolik: {str(e)}")
    finally:
        cleanup_directory(temp_dir)
        try:
            await status_msg.delete()
        except Exception:
            pass
