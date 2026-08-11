import asyncio
import os
import re
import uuid
from aiogram import Router
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    ChosenInlineResult, FSInputFile, InputMediaAudio,
)
from utils.music_search import SEARCH_CACHE, search_youtube_flat, download_yt_audio_sync, auto_cleanup_search_cache
from utils.downloader import cleanup_directory

router = Router()


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    query = (inline_query.query or "").strip()
    if not query:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    loop = asyncio.get_event_loop()
    try:
        entries = await loop.run_in_executor(None, search_youtube_flat, query, 5)
    except Exception:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    if not entries:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    search_id = str(uuid.uuid4())[:8]
    SEARCH_CACHE[search_id] = {i + 1: e for i, e in enumerate(entries)}
    asyncio.create_task(auto_cleanup_search_cache(search_id))

    results = []
    for idx, entry in enumerate(entries, 1):
        results.append(InlineQueryResultArticle(
            id=f"{search_id}:{idx}",
            title=entry["title"][:128],
            description=f"⏱ {entry['duration_str']} • YouTube",
            input_message_content=InputTextMessageContent(
                message_text=f"🎵 {entry['title']}\n⏳ Yuklanmoqda...",
            ),
        ))

    await inline_query.answer(results, cache_time=30, is_personal=True)


@router.chosen_inline_result()
async def handle_chosen_inline(chosen: ChosenInlineResult):
    result_id = chosen.result_id
    if ":" not in result_id:
        return

    search_id, idx_str = result_id.split(":", 1)
    try:
        idx = int(idx_str)
    except ValueError:
        return

    song_info = SEARCH_CACHE.get(search_id, {}).get(idx)
    if not song_info:
        return

    bot = chosen.bot
    title = song_info["title"]
    loop = asyncio.get_event_loop()
    temp_dir = None

    try:
        temp_dir, audio_path = await loop.run_in_executor(
            None, download_yt_audio_sync, song_info["video_id"]
        )
        if not audio_path or not os.path.exists(audio_path):
            if chosen.inline_message_id:
                await bot.edit_message_text(
                    "❌ Qo'shiqni yuklab bo'lmadi.",
                    inline_message_id=chosen.inline_message_id,
                )
            return

        safe = re.sub(r'[^\w\s-]', '', title[:50]).strip() or "song"
        audio_file = FSInputFile(audio_path, filename=f"{safe}.mp3")
        caption = f"🎵 {title[:200]}"

        if chosen.inline_message_id:
            await bot.edit_message_media(
                media=InputMediaAudio(media=audio_file, caption=caption),
                inline_message_id=chosen.inline_message_id,
            )
        else:
            await bot.send_audio(
                chat_id=chosen.from_user.id,
                audio=audio_file,
                caption=caption,
            )
    except Exception as e:
        if chosen.inline_message_id:
            try:
                await bot.edit_message_text(
                    f"❌ Xatolik: {str(e)}",
                    inline_message_id=chosen.inline_message_id,
                )
            except Exception:
                pass
    finally:
        if temp_dir:
            cleanup_directory(temp_dir)
