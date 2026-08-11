import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import config

DB_PATH = config.BASE_DIR / "history.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER NOT NULL,
                activity_date TEXT NOT NULL,
                PRIMARY KEY (user_id, activity_date)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_downloads_user_date
            ON downloads (user_id, created_at)
        """)
        conn.commit()


def record_download(user_id: int, platform: str, title: str, url: str) -> str:
    init_db()
    record_id = str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO downloads (id, user_id, platform, title, url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (record_id, user_id, platform, title[:500], url, now),
        )
        conn.execute(
            "INSERT OR IGNORE INTO user_activity (user_id, activity_date) VALUES (?, ?)",
            (user_id, today),
        )
        conn.commit()
    return record_id


def get_user_history(user_id: int, limit: int = 20) -> List[dict]:
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, platform, title, url, created_at FROM downloads "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_download_by_id(record_id: str, user_id: int) -> Optional[dict]:
    init_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT id, platform, title, url, created_at FROM downloads WHERE id = ? AND user_id = ?",
            (record_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def get_total_downloads() -> int:
    init_db()
    with _get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]


def get_platform_stats() -> dict:
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT platform, COUNT(*) as cnt FROM downloads GROUP BY platform ORDER BY cnt DESC"
        ).fetchall()
    return {r["platform"]: r["cnt"] for r in rows}


def get_today_active_users() -> int:
    init_db()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE activity_date = ?",
            (today,),
        ).fetchone()[0]


def get_activity_last_n_days(days: int = 7) -> dict:
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT activity_date, COUNT(DISTINCT user_id) as cnt "
            "FROM user_activity GROUP BY activity_date ORDER BY activity_date DESC LIMIT ?",
            (days,),
        ).fetchall()
    result = {r["activity_date"]: r["cnt"] for r in rows}
    # Oxirgi N kunni to'ldirish
    from datetime import timedelta
    today = datetime.now(timezone.utc).date()
    filled = {}
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        filled[d] = result.get(d, 0)
    return filled
