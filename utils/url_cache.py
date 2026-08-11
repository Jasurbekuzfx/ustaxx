import asyncio
import hashlib
import time
from typing import Any, Dict, Optional

# url_hash -> {url, platform, user_id, kind, username, quality, created_at}
URL_CACHE: Dict[str, Dict[str, Any]] = {}

CACHE_TTL = 1800  # 30 daqiqa


def store_url(url: str, platform: str, user_id: int, kind: str = "media", username: str = None) -> str:
    """URL'ni cache'ga saqlaydi va qisqa hash qaytaradi."""
    url_hash = hashlib.md5(f"{user_id}:{url}:{time.time()}".encode()).hexdigest()[:8]
    URL_CACHE[url_hash] = {
        "url": url,
        "platform": platform,
        "user_id": user_id,
        "kind": kind,
        "username": username,
        "created_at": time.time(),
    }
    asyncio.create_task(_cleanup_url_cache(url_hash, CACHE_TTL))
    return url_hash


def get_cached_url(url_hash: str) -> Optional[Dict[str, Any]]:
    entry = URL_CACHE.get(url_hash)
    if not entry:
        return None
    if time.time() - entry["created_at"] > CACHE_TTL:
        URL_CACHE.pop(url_hash, None)
        return None
    return entry


async def _cleanup_url_cache(url_hash: str, delay: int):
    await asyncio.sleep(delay)
    URL_CACHE.pop(url_hash, None)
