from typing import Optional

from utils.history import (
    get_activity_last_n_days,
    get_platform_stats,
    get_today_active_users,
    get_total_downloads,
)
from utils.platforms import PLATFORM_LABELS
from utils.user_manager import get_users_count


def get_extended_stats() -> dict:
    platform_stats = get_platform_stats()
    top_platform = None
    top_count = 0
    for platform, count in platform_stats.items():
        if count > top_count:
            top_platform = platform
            top_count = count

    return {
        "total_users": get_users_count(),
        "today_active": get_today_active_users(),
        "total_downloads": get_total_downloads(),
        "top_platform": top_platform,
        "top_platform_label": PLATFORM_LABELS.get(top_platform, top_platform or "—"),
        "top_platform_count": top_count,
        "platform_stats": platform_stats,
        "activity_7d": get_activity_last_n_days(7),
    }


def format_stats_text(stats: Optional[dict] = None) -> str:
    if stats is None:
        stats = get_extended_stats()

    lines = [
        "📊 <b>Bot Statistikasi</b>\n",
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']}",
        f"📅 <b>Bugungi faol foydalanuvchilar:</b> {stats['today_active']}",
        f"📥 <b>Jami yuklamalar:</b> {stats['total_downloads']}",
        f"🏆 <b>Eng ko'p ishlatilgan platforma:</b> {stats['top_platform_label']} ({stats['top_platform_count']})",
    ]

    if stats["platform_stats"]:
        lines.append("\n<b>Platformalar bo'yicha:</b>")
        for platform, count in sorted(stats["platform_stats"].items(), key=lambda x: -x[1]):
            label = PLATFORM_LABELS.get(platform, platform)
            lines.append(f"  • {label}: {count}")

    return "\n".join(lines)


def generate_activity_chart(output_path: str) -> bool:
    """Oxirgi 7 kunlik faollik grafigini yaratadi."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime

        activity = get_activity_last_n_days(7)
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in activity.keys()]
        counts = list(activity.values())

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(dates, counts, color="#4A90D9", width=0.6)
        ax.set_xlabel("Sana")
        ax.set_ylabel("Faol foydalanuvchilar")
        ax.set_title("Oxirgi 7 kunlik faollik")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        fig.autofmt_xdate()
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
        return True
    except Exception as e:
        print(f"Grafik yaratishda xatolik: {e}")
        return False
