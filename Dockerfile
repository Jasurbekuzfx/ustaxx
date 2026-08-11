FROM python:3.11-slim

# Tizim paketlarini yangilash va ffmpeg o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Ishchi katalogni yaratish
WORKDIR /app

# Kutubxonalar ro'yxatini ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyihaning barcha fayllarini ko'chirish
COPY . .

# Botni ishga tushirish buyrug'i
CMD ["python", "bot.py"]
