import json
import os
from typing import List

import config

CHANNELS_FILE = config.BASE_DIR / "channels.json"


def load_channels() -> List[dict]:
    if not os.path.exists(CHANNELS_FILE):
        return []
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Kanallar ro'yxatini o'qishda xatolik: {e}")
        return []


def save_channels(channels: List[dict]):
    try:
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Kanallar ro'yxatini saqlashda xatolik: {e}")


def add_channel(channel_id: str, title: str = "") -> bool:
    channels = load_channels()
    channel_id = channel_id.strip()
    if any(c["id"] == channel_id for c in channels):
        return False
    channels.append({"id": channel_id, "title": title or channel_id})
    save_channels(channels)
    return True


def remove_channel(channel_id: str) -> bool:
    channels = load_channels()
    channel_id = channel_id.strip()
    new_channels = [c for c in channels if c["id"] != channel_id]
    if len(new_channels) == len(channels):
        return False
    save_channels(new_channels)
    return True


def get_channel_ids() -> List[str]:
    return [c["id"] for c in load_channels()]
