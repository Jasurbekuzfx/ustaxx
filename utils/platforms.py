import re
from typing import Optional, Tuple

# Platforma nomlari
INSTAGRAM = "instagram"
TIKTOK = "tiktok"
FACEBOOK = "facebook"
PINTEREST = "pinterest"
SNAPCHAT = "snapchat"
LIKEE = "likee"
THREADS = "threads"
YOUTUBE_SHORTS = "youtube_shorts"
YOUTUBE = "youtube"

PLATFORM_LABELS = {
    INSTAGRAM: "Instagram",
    TIKTOK: "TikTok",
    FACEBOOK: "Facebook",
    PINTEREST: "Pinterest",
    SNAPCHAT: "Snapchat",
    LIKEE: "Likee",
    THREADS: "Threads",
    YOUTUBE_SHORTS: "YouTube Shorts",
    YOUTUBE: "YouTube",
}

# Tartib muhim: aniqroq patternlar avval
PLATFORM_PATTERNS: list[Tuple[str, re.Pattern]] = [
    (INSTAGRAM, re.compile(
        r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv|reels)/[^\s?]+",
        re.IGNORECASE,
    )),
    (TIKTOK, re.compile(
        r"https?://(?:www\.)?(?:tiktok\.com/@[^\s/]+/video/\d+[^\s?]*"
        r"|(?:vm\.tiktok\.com|vt\.tiktok\.com|douyin\.com|tiktok\.com/(?!@))[^\s?]+)",
        re.IGNORECASE,
    )),
    (FACEBOOK, re.compile(
        r"https?://(?:www\.|m\.)?facebook\.com/(?:reel|watch|photo|video|share|story)/[^\s?]+"
        r"|https?://fb\.watch/[^\s?]+"
        r"|https?://(?:www\.)?facebook\.com/[^\s?]+/videos/[^\s?]+",
        re.IGNORECASE,
    )),
    (PINTEREST, re.compile(
        r"https?://(?:www\.)?pinterest\.(?:com|it|fr|de|jp|co\.uk|es|ca|com\.au)/pin/[^\s?]+"
        r"|https?://pin\.it/[^\s?]+",
        re.IGNORECASE,
    )),
    (SNAPCHAT, re.compile(
        r"https?://(?:www\.)?snapchat\.com/(?:add|t|spotlight|story|discover)/[^\s?]+"
        r"|https?://story\.snapchat\.com/[^\s?]+",
        re.IGNORECASE,
    )),
    (LIKEE, re.compile(
        r"https?://(?:www\.)?(?:likee\.video|l\.likee\.video|likee\.com)/[^\s?]+",
        re.IGNORECASE,
    )),
    (THREADS, re.compile(
        r"https?://(?:www\.)?threads\.(?:net|com)/@[^\s/]+/post/[^\s?]+",
        re.IGNORECASE,
    )),
    (YOUTUBE_SHORTS, re.compile(
        r"https?://(?:www\.)?youtube\.com/shorts/[^\s?]+"
        r"|https?://youtu\.be/[^\s?]+",
        re.IGNORECASE,
    )),
    (YOUTUBE, re.compile(
        r"https?://(?:www\.|music\.)?youtube\.com/watch\?v=[^\s?&]+",
        re.IGNORECASE,
    )),
]

# Profil va story havolalari: (platforma, kind, regex, url_builder)
# kind: "profile" (oxirgi N ta media) yoki "story" (barcha story'lar)
PROFILE_PATTERNS: list[Tuple[str, str, re.Pattern]] = [
    (INSTAGRAM, "story", re.compile(
        r"https?://(?:www\.)?instagram\.com/stories/([a-zA-Z0-9._]{1,30})(?:/\d+)?",
        re.IGNORECASE,
    )),
    (TIKTOK, "profile", re.compile(
        r"https?://(?:www\.)?tiktok\.com/@([a-zA-Z0-9._]{1,30})",
        re.IGNORECASE,
    )),
    (INSTAGRAM, "profile", re.compile(
        r"https?://(?:www\.)?instagram\.com/"
        r"(?!p/|reel/|reels/|tv/|stories/|explore/|accounts/|direct/|shop/|about/|help/)"
        r"(?:@)?([a-zA-Z0-9._]{1,30})",
        re.IGNORECASE,
    )),
]


def _build_profile_url(platform: str, kind: str, match: re.Match) -> str:
    username = match.group(1)
    if kind == "story":
        return f"https://www.instagram.com/stories/{username}/"
    if platform == INSTAGRAM:
        return f"https://www.instagram.com/{username}/"
    if platform == TIKTOK:
        return f"https://www.tiktok.com/@{username}/"
    return match.group(0)


def detect_platform(text: str) -> Optional[Tuple[str, str]]:
    """
    Matndan platforma va havolani aniqlaydi.
    Qaytadi: (platform_name, url) yoki None
    """
    text = text.strip()
    for platform, pattern in PLATFORM_PATTERNS:
        match = pattern.search(text)
        if match:
            return platform, match.group(0)
    return None


def analyze_url(text: str) -> Optional[Tuple[str, str, str, Optional[str]]]:
    """
    Havolani to'liq tahlil qiladi.
    Qaytadi: (platform, kind, url, username) yoki None
    kind: "media" | "profile" | "story"
    """
    text = text.strip()
    for platform, pattern in PLATFORM_PATTERNS:
        match = pattern.search(text)
        if match:
            return platform, "media", match.group(0), None
    for platform, kind, pattern in PROFILE_PATTERNS:
        match = pattern.search(text)
        if match:
            url = _build_profile_url(platform, kind, match)
            return platform, kind, url, match.group(1)
    return None


def is_supported_url(text: str) -> bool:
    return detect_platform(text) is not None
