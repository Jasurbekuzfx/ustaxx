import asyncio
import datetime
import os
import zipfile

import config

BACKUP_DIR = config.BASE_DIR / "backups"
RETENTION_DAYS = 14


def _files_to_backup() -> list:
    candidates = [
        config.HISTORY_DB,
        config.USERS_FILE,
        config.ADMINS_FILE,
        config.CHANNELS_FILE,
    ]
    return [f for f in candidates if os.path.exists(f)]


def create_backup() -> str:
    """history.db va JSON fayllarni ZIP'ga siqib saqlaydi. Zip manzilini qaytaradi."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = str(BACKUP_DIR / f"backup_{stamp}.zip")
    files = _files_to_backup()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(str(f), arcname=os.path.basename(str(f)))
    cleanup_old_backups()
    return zip_path


def cleanup_old_backups(keep_days: int = RETENTION_DAYS):
    """RETENTION_DAYS'dan eski zaxira fayllarini o'chiradi."""
    try:
        cutoff = datetime.datetime.now().timestamp() - keep_days * 86400
        for name in os.listdir(BACKUP_DIR):
            path = os.path.join(BACKUP_DIR, name)
            if name.endswith(".zip") and os.path.getmtime(path) < cutoff:
                try:
                    os.remove(path)
                except OSError:
                    pass
    except OSError:
        pass


async def daily_backup_task():
    """Har kuni 00:00 da avtomatik zaxira oladi."""
    while True:
        now = datetime.datetime.now()
        next_midnight = (now + datetime.timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep(max((next_midnight - now).total_seconds(), 1))
        try:
            path = create_backup()
            print(f"💾 Avtomatik zaxira yaratildi: {path}")
        except Exception as e:
            print(f"💾 Avtomatik zaxirada xatolik: {e}")