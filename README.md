# Telegram Media Downloader & Shazam Bot

Ushbu Telegram bot quyidagi platformalardan media yuklab beradi: **Instagram, TikTok, Facebook, Pinterest, Snapchat, Likee, Threads, YouTube Shorts**. Shuningdek, Shazam orqali qo'shiq aniqlash, qo'shiq qidirish, inline rejim va yuklab olish tarixi mavjud.

## ✨ Imkoniyatlar

- 📥 **8 ta platforma** — havola yuboring, sifat tanlang (720p / 1080p / Audio)
- 🔍 **Shazam** — voice, audio yoki videodan qo'shiq aniqlash
- 🎵 **Qo'shiq qidirish** — nom yozing yoki inline rejimda `@bot_username qoshiq`
- 📜 **Tarix** — `/history` orqali oxirgi 20 ta yuklab olish
- 📡 **Majburiy obuna** — kanallarga obuna tekshiruvi
- 📊 **Kengaytirilgan statistika** — adminlar uchun `/stats`

## 🚀 Texnologiyalar
- **Til:** Python 3.11+
- **Kutubxona:** aiogram 3.x (asinxron bot yaratish uchun)
- **Media yuklash:** yt-dlp (Instagram va TikTok uchun)
- **Audio tanish:** shazamio (Shazam API bilan ishlash uchun)
- **Fayllarni qayta ishlash:** ffmpeg (audioni ajratish va katta videolarni siqish uchun)

---

## 🛠 O'rnatish va Sozlash

### 1. Tizim talablari (FFmpeg)
Loyihada videolarni siqish va audiolarni ajratish uchun `ffmpeg` dasturi bo'lishi shart.

#### **Ubuntu/Debian VPS:**
```bash
sudo apt update
sudo apt install ffmpeg -y
```

#### **Windows:**
1. [ffmpeg.org](https://ffmpeg.org/download.html) saytidan yuklab oling.
2. Yuklab olingan fayllarni biror papkaga (masalan `C:\ffmpeg`) joylashtiring.
3. Path tizim o'zgaruvchilariga (Environment Variables) `C:\ffmpeg\bin` manzilini qo'shing.

---

### 2. Loyihani ishga tushirish (Mahalliy yoki VPS da)

1. Loyiha papkasiga kiring:
   ```bash
   cd ustax
   ```

2. Virtual muhit yaratish va uni faollashtirish:
   ```bash
   python -m venv venv
   # Windows uchun:
   venv\Scripts\activate
   # Linux/macOS uchun:
   source venv/bin/activate
   ```

3. Kutubxonalarni o'rnatish:
   ```bash
   pip install -r requirements.txt
   ```

4. Konfiguratsiya faylini yaratish:
   `.env.example` faylidan `.env` nusxasini yarating va uni tahrirlang:
   ```bash
   cp .env.example .env
   ```
   `.env` fayli tarkibi:
   ```env
   BOT_TOKEN=Sizning_Telegram_Bot_Tokeningiz
   IG_COOKIES_PATH=cookies.txt
   RATE_LIMIT_LIMIT=5
   RATE_LIMIT_WINDOW=60
   ```

5. **Instagram Cookies (Majburiy emas, lekin tavsiya etiladi):**
   Instagram login yoki yopiq sahifalardagi videolarni yuklashda xatolik bermasligi uchun brauzeringizdan `cookies.txt` formatida eksport qilib oling (masalan, brauzerga "Get cookies.txt" plagini orqali). Olingan faylni loyihaning asosiy papkasida `cookies.txt` nomi bilan saqlang.

6. Botni ishga tushirish:
   ```bash
   python bot.py
   ```

---

## 🐳 Docker orqali ishga tushirish (Tavsiya etiladi)

Docker yordamida loyihani VPS da tez va ortiqcha muammolarsiz ishga tushirish mumkin (Docker o'z ichida `ffmpeg`ni avtomat o'rnatib oladi):

1. `.env` faylini to'ldiring.
2. (Ixtiyoriy) Agar cookies bo'lsa, `cookies.txt` faylini loyiha papkasiga joylashtiring (bo'lmasa bo'sh fayl yaratib qo'ying: `touch cookies.txt`).
3. Konteynerni ishga tushiring:
   ```bash
   docker compose up -d --build
   ```
4. Loglarni ko'rish:
   ```bash
   docker compose logs -f
   ```

---

## ⚙️ Linux Systemd xizmati sifatida sozlash (Docker ishlatilmasa)

Botni VPS da fonda doimiy ishlab turishi uchun systemd xizmati sifatida sozlash mumkin:

1. Xizmat faylini yarating:
   ```bash
   sudo nano /etc/systemd/system/tgbot.service
   ```

2. Quyidagi matnni nusxalab joylashtiring (yo'llarni o'zgartiring):
   ```ini
   [Unit]
   Description=Telegram Media Downloader Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/ustax
   ExecStart=/home/ubuntu/ustax/venv/bin/python bot.py
   Restart=always
   RestartSec=5

   [Install]
   WantedBy=multi-user.target
   ```

3. Xizmatni faollashtiring va ishga tushiring:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tgbot
   sudo systemctl start tgbot
   ```

4. Statusni tekshirish:
   ```bash
   sudo systemctl status tgbot
   ```

---

## 📡 Majburiy kanal obunasi

Admin panel orqali majburiy kanallar qo'shish mumkin:

```bash
/addchannel @kanal_username
/removechannel @kanal_username
/channels
```

> ⚠️ **Muhim:** Bot majburiy kanallarda **admin** bo'lishi kerak. Aks holda `get_chat_member()` obunani tekshira olmaydi va foydalanuvchilar bloklanadi.

---

## 🔎 Inline rejim

Inline rejimdan foydalanish uchun BotFather'da yoqing:

1. [@BotFather](https://t.me/BotFather) ga `/setinline` yuboring
2. Botingizni tanlang
3. Placeholder matn kiriting (masalan: `Qo'shiq nomini yozing...`)

Foydalanish: istalgan chatda `@bot_username qoshiq nomi` deb yozing va natijadan birini tanlang.

---

## 👑 Admin buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/admin` | Admin panel |
| `/stats` | Kengaytirilgan statistika + 7 kunlik grafik |
| `/broadcast` | Barcha foydalanuvchilarga xabar |
| `/addchannel` | Majburiy kanal qo'shish |
| `/removechannel` | Kanalni o'chirish |
| `/addadmin` | Admin qo'shish (Super Admin) |
| `/removeadmin` | Adminni o'chirish (Super Admin) |
