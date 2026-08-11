import asyncio
import os
import shutil
import uuid
import aiohttp
import yt_dlp
import config
from utils.platforms import (
    INSTAGRAM, TIKTOK, FACEBOOK, PINTEREST, SNAPCHAT,
    LIKEE, THREADS, YOUTUBE_SHORTS,
)

VIDEO_EXTENSIONS = (".mp4", ".mkv", ".mov", ".avi", ".webm")
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".ogg", ".wav", ".aac")

QUALITY_FORMATS = {
    "720": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "audio": "bestaudio/best",
}


class DownloadResult:
    def __init__(
        self,
        success: bool,
        file_paths: list = None,
        audio_path: str = None,
        title: str = "",
        error: str = None,
        platform: str = "",
    ):
        self.success = success
        self.file_paths = file_paths or []
        self.audio_path = audio_path
        self.title = title
        self.error = error
        self.platform = platform


async def get_video_duration(file_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        if process.returncode == 0:
            return float(stdout.decode().strip())
    except Exception as e:
        print(f"Video davomiyligini aniqlashda xatolik: {e}")
    return 0.0


async def compress_video(input_path: str, output_path: str, target_size_mb: int = 48) -> bool:
    duration = await get_video_duration(input_path)
    if duration <= 0:
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vcodec", "libx264", "-crf", "30", "-preset", "fast",
            "-acodec", "aac", "-b:a", "128k", output_path,
        ]
    else:
        target_size_bits = target_size_mb * 1024 * 1024 * 8
        audio_bitrate = 128000
        video_bitrate = max(int(target_size_bits / duration) - audio_bitrate, 150000)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-b:v", f"{video_bitrate}", "-vcodec", "libx264", "-preset", "fast",
            "-b:a", "128k", "-acodec", "aac", output_path,
        ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        print(f"Videoni siqishda xatolik: {e}")
        return False


async def extract_audio_from_video(video_path: str, audio_path: str) -> bool:
    cmd = [
        "ffmpeg", "-y", "-i", video_path, "-vn",
        "-acodec", "libmp3lame", "-q:a", "2", audio_path,
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        print(f"Videodan audio ajratishda xatolik: {e}")
        return False


def _get_cookies_file(platform: str = None):
    tmp_cookies = "/tmp/youtube_cookies.txt"
    if os.path.exists(tmp_cookies):
        return tmp_cookies
    if platform == INSTAGRAM and config.IG_COOKIES_PATH and os.path.exists(config.IG_COOKIES_PATH):
        return config.IG_COOKIES_PATH
    return None



def _build_ydl_opts(download_dir: str, platform: str, quality: str = "1080") -> dict:
    cookies_file = _get_cookies_file(platform)
    opts = {
        "outtmpl": os.path.join(download_dir, "%(autonumber)02d_%(title).50s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    if cookies_file:
        opts["cookiefile"] = cookies_file

    import logging
    cookie_param_str = opts.get("cookiefile", "None (Fayl topilmadi)")
    print(f"🍪 [downloader.py] yt-dlp cookiefile: {cookie_param_str}")
    logging.info(f"🍪 [downloader.py] yt-dlp cookiefile: {cookie_param_str}")

    if quality == "audio":
        opts["format"] = QUALITY_FORMATS["audio"]
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        fmt = QUALITY_FORMATS.get(quality, QUALITY_FORMATS["1080"])
        opts["format"] = fmt

    # Platformaga xos sozlamalar
    if platform in (TIKTOK, LIKEE, SNAPCHAT):
        opts.setdefault("http_headers", {})
        opts["http_headers"]["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    return opts


async def download_tiktok_tikwm(url: str, output_dir: str) -> dict:
    api_url = "https://www.tikwm.com/api/"
    params = {"url": url, "hd": "1"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": "TikWM API javob bermadi"}
                res = await resp.json()
                if res.get("code") != 0:
                    return {"error": res.get("msg", "Videoni yuklab bo'lmadi")}
                data = res.get("data", {})
                video_url = data.get("play")
                music_url = data.get("music")
                title = data.get("title", "")
                video_path = music_path = None
                if video_url:
                    video_path = os.path.join(output_dir, "video.mp4")
                    async with session.get(video_url) as vr:
                        if vr.status == 200:
                            with open(video_path, "wb") as f:
                                f.write(await vr.read())
                        else:
                            video_path = None
                if music_url:
                    music_path = os.path.join(output_dir, "audio.mp3")
                    async with session.get(music_url) as mr:
                        if mr.status == 200:
                            with open(music_path, "wb") as f:
                                f.write(await mr.read())
                        else:
                            music_path = None
                return {"video_path": video_path, "music_path": music_path, "title": title}
    except Exception as e:
        return {"error": f"TikWM API xatoligi: {str(e)}"}


def _run_yt_dlp(url: str, ydl_opts: dict) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.sanitize_info(info)


async def _process_downloaded_files(
    download_dir: str,
    downloaded_files: list,
    title: str,
    quality: str,
    platform: str,
) -> DownloadResult:
    if not downloaded_files:
        return DownloadResult(success=False, error="Yuklab olingan fayllar topilmadi.", platform=platform)

    processed_files = []
    for file_path in downloaded_files:
        ext = os.path.splitext(file_path)[1].lower()
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50 and ext in VIDEO_EXTENSIONS:
            compressed_path = file_path.replace(ext, f"_compressed{ext}")
            success = await compress_video(file_path, compressed_path)
            if success:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                processed_files.append(compressed_path)
            else:
                processed_files.append(file_path)
        else:
            processed_files.append(file_path)

    audio_path = None
    if quality == "audio":
        audio_files = [f for f in processed_files if f.lower().endswith(AUDIO_EXTENSIONS)]
        if audio_files:
            audio_path = audio_files[0]
            return DownloadResult(
                success=True, file_paths=[], audio_path=audio_path,
                title=title, platform=platform,
            )
    else:
        video_files = [f for f in processed_files if f.lower().endswith(VIDEO_EXTENSIONS)]
        if video_files:
            possible_audio = os.path.join(download_dir, "extracted_audio.mp3")
            if await extract_audio_from_video(video_files[0], possible_audio):
                audio_path = possible_audio

    return DownloadResult(
        success=True,
        file_paths=processed_files if quality != "audio" else [],
        audio_path=audio_path,
        title=title,
        platform=platform,
    )


async def universal_download(url: str, platform: str, quality: str = "1080") -> DownloadResult:
    """
    Universal yuklab olish funksiyasi — barcha platformalar uchun.
    quality: '720', '1080', 'audio'
    """
    unique_id = str(uuid.uuid4())
    download_dir = os.path.join(config.TEMP_DIR, unique_id)
    os.makedirs(download_dir, exist_ok=True)

    try:
        # TikTok va Likee uchun avval TikWM API
        if platform in (TIKTOK, LIKEE) and quality != "audio":
            tikwm_res = await download_tiktok_tikwm(url, download_dir)
            if "error" not in tikwm_res and tikwm_res.get("video_path"):
                video_path = tikwm_res["video_path"]
                music_path = tikwm_res["music_path"]
                title = tikwm_res["title"]
                file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                if file_size_mb > 50:
                    compressed = os.path.join(download_dir, "video_compressed.mp4")
                    if await compress_video(video_path, compressed):
                        video_path = compressed
                return DownloadResult(
                    success=True,
                    file_paths=[video_path],
                    audio_path=music_path,
                    title=title,
                    platform=platform,
                )

        ydl_opts = _build_ydl_opts(download_dir, platform, quality)
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _run_yt_dlp, url, ydl_opts)

        downloaded_files = sorted([
            os.path.join(download_dir, f)
            for f in os.listdir(download_dir)
            if os.path.isfile(os.path.join(download_dir, f))
        ])
        title = info.get("title", "") if info else ""
        return await _process_downloaded_files(download_dir, downloaded_files, title, quality, platform)

    except Exception as e:
        try:
            shutil.rmtree(download_dir)
        except OSError:
            pass
        return DownloadResult(success=False, error=str(e), platform=platform)


async def download_media(url: str, quality: str = "1080") -> DownloadResult:
    """Orqaga moslik uchun wrapper — platformani avtomatik aniqlaydi."""
    from utils.platforms import detect_platform
    detected = detect_platform(url)
    if not detected:
        return DownloadResult(success=False, error="Platforma aniqlanmadi.")
    platform, clean_url = detected
    return await universal_download(clean_url, platform, quality)


async def download_profile(url: str, platform: str, quality: str = "1080", limit: int = 5) -> DownloadResult:
    """
    Profil (Instagram/TikTok) yoki story'dan oxirgi N ta mediani yuklab oladi.
    Audio sifati profillar uchun qo'llab-quvvatlanmaydi — '1080' ga tushiriladi.
    """
    if quality == "audio":
        quality = "1080"

    unique_id = str(uuid.uuid4())
    download_dir = os.path.join(config.TEMP_DIR, unique_id)
    os.makedirs(download_dir, exist_ok=True)

    try:
        ydl_opts = _build_ydl_opts(download_dir, platform, quality)
        ydl_opts["playlistend"] = limit
        ydl_opts["ignoreerrors"] = True
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _run_yt_dlp, url, ydl_opts)

        downloaded_files = sorted([
            os.path.join(download_dir, f)
            for f in os.listdir(download_dir)
            if os.path.isfile(os.path.join(download_dir, f))
        ])
        title = info.get("title", "") if info else f"{platform} profili"
        return await _process_downloaded_files(download_dir, downloaded_files, title, quality, platform)
    except Exception as e:
        try:
            shutil.rmtree(download_dir)
        except OSError:
            pass
        return DownloadResult(success=False, error=str(e), platform=platform)


def cleanup_directory(directory_path: str):
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
    except Exception as e:
        print(f"Papkani tozalashda xatolik: {e}")
