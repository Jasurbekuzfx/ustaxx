import asyncio
import os
import uuid
import yt_dlp

import config

SEARCH_CACHE = {}


def _get_cookies_file():
    tmp_cookies = "/tmp/youtube_cookies.txt"
    if os.path.exists(tmp_cookies):
        return tmp_cookies
    return None


def search_youtube_flat(query: str, limit: int = 10) -> list:
    import logging
    ydl_opts = {
        'extract_flat': True, 'skip_download': True,
        'quiet': True, 'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'mweb']}},
    }
    cookies_file = _get_cookies_file()
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    cookie_param_str = ydl_opts.get("cookiefile", "None (Fayl topilmadi)")
    print(f"🍪 [music_search.py - search] yt-dlp cookiefile: {cookie_param_str}")
    logging.info(f"🍪 [music_search.py - search] yt-dlp cookiefile: {cookie_param_str}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    entries = info.get("entries", []) if info else []
    results = []
    for entry in entries:
        if not entry:
            continue
        video_id = entry.get("id")
        title = entry.get("title") or "Noma'lum qo'shiq"
        artist = entry.get("artist") or entry.get("uploader") or entry.get("channel") or ""
        duration = entry.get("duration") or 0
        if video_id and duration <= 900:
            results.append({
                "video_id": video_id,
                "title": title,
                "artist": artist,
                "duration_str": f"{int(duration // 60):02d}:{int(duration % 60):02d}",
                "duration": duration,
            })
    return results


def download_yt_audio_sync(video_id: str) -> tuple:
    import logging
    unique_id = str(uuid.uuid4())
    download_dir = os.path.join(config.TEMP_DIR, unique_id)
    os.makedirs(download_dir, exist_ok=True)
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_dir, "%(title).50s.%(ext)s"),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True, 'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'mweb']}},
    }
    cookies_file = _get_cookies_file()
    if cookies_file:
        ydl_opts["cookiefile"] = cookies_file

    cookie_param_str = ydl_opts.get("cookiefile", "None (Fayl topilmadi)")
    print(f"🍪 [music_search.py - download] yt-dlp cookiefile: {cookie_param_str}")
    logging.info(f"🍪 [music_search.py - download] yt-dlp cookiefile: {cookie_param_str}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    audio_path = next(
        (os.path.join(download_dir, f) for f in os.listdir(download_dir) if f.endswith(".mp3")),
        None,
    )
    return download_dir, audio_path


async def auto_cleanup_search_cache(search_id: str, delay: int = 1800):
    await asyncio.sleep(delay)
    SEARCH_CACHE.pop(search_id, None)
