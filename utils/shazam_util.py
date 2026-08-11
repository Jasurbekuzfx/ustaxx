import asyncio
import urllib.parse
from shazamio import Shazam
import os

# Initialize Shazam client
shazam = Shazam()

async def extract_audio_from_video(video_path: str, audio_path: str) -> bool:
    """
    Video fayldan birinchi 30 soniyalik audioni ajratib oladi va MP3 formatda saqlaydi.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ss", "00:00:00",
        "-t", "30",
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",  # Shazam uchun optimal chastota
        "-ac", "1",      # Mono kanal
        audio_path
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        print(f"Ffmpeg orqali audio ajratishda xatolik: {e}")
        return False

async def identify_audio(file_path: str) -> dict:
    """
    Shazamio orqali audio faylni aniqlaydi va kerakli ma'lumotlarni qaytaradi.
    """
    if not os.path.exists(file_path):
        return None

    try:
        # Shazam orqali aniqlash
        out = await shazam.recognize(file_path)
        
        if not out or not out.get("track"):
            return None

        track = out["track"]
        title = track.get("title", "Noma'lum qo'shiq")
        artist = track.get("subtitle", "Noma'lum ijrochi")
        
        # Albom rasmi (coverart)
        images = track.get("images", {})
        coverart = images.get("coverart") or images.get("coverarthq") or images.get("background")
        
        # Shazam sahifasi havolasi
        share_info = track.get("share", {})
        shazam_url = share_info.get("href")
        
        # Spotify va YouTube Music uchun qidiruv havolalarini yaratamiz
        # Chunki API har doim ham tayyor havolalarni qaytarmasligi mumkin
        search_query = f"{artist} {title}"
        encoded_query = urllib.parse.quote(search_query)
        
        spotify_url = f"https://open.spotify.com/search/{encoded_query}"
        yt_music_url = f"https://music.youtube.com/search?q={encoded_query}"
        
        # Hub orqali Apple Music yoki boshqa platformalarni ham tekshirish mumkin
        apple_music_url = None
        hub = track.get("hub", {})
        for action in hub.get("actions", []):
            if action.get("name") == "apple" and action.get("uri"):
                apple_music_url = action.get("uri")
                break

        return {
            "title": title,
            "artist": artist,
            "coverart": coverart,
            "shazam_url": shazam_url,
            "spotify_url": spotify_url,
            "yt_music_url": yt_music_url,
            "apple_music_url": apple_music_url
        }

    except Exception as e:
        print(f"Shazam aniqlash xatoligi: {e}")
        return None
