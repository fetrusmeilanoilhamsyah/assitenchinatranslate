# 🌐 Professional Telegram Translator Bot

Bot translator Telegram professional untuk terjemahan **Indonesia ↔ China** dan **Indonesia ↔ English**.

## ✨ Fitur

- 🇮🇩 ↔ 🇨🇳 Terjemahan Indonesia - China (Mandarin)
- 🇮🇩 ↔ 🇬🇧 Terjemahan Indonesia - English
- ⚡ Respon cepat dan akurat
- 🛡️ Anti-crash dengan error handling proper
- 📊 Statistik penggunaan
- 🚀 Lightweight untuk VPS kecil
- 🔒 Rate limiting built-in

## 📁 Struktur Folder

```
translator-bot/
├── bot.py              # Main bot file
├── config.py           # Configuration
├── utils.py            # Utility functions
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── .gitignore         # Git ignore rules
├── README.md          # Documentation
├── logs/              # Log files (auto-created)
└── data/              # Stats data (auto-created)
```

## 🚀 Instalasi

### 1. Clone atau Download

```bash
cd translator-bot
```

### 2. Setup Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment

```bash
cp .env.example .env
nano .env  # Edit dengan token bot lu
```

**Isi `.env`:**
```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
RATE_LIMIT_SECONDS=2
MAX_TEXT_LENGTH=1000
LOG_LEVEL=INFO
```

### 5. Dapatkan Bot Token

1. Chat ke [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot`
3. Ikuti instruksi
4. Copy token yang diberikan
5. Paste ke `.env` file

## 🎮 Menjalankan Bot

### Development (Foreground)

```bash
python bot.py
```

### Production (Background dengan nohup)

```bash
nohup python bot.py > /dev/null 2>&1 &
```

### Production (dengan systemd - Recommended)

Buat service file `/etc/systemd/system/translator-bot.service`:

```ini
[Unit]
Description=Telegram Translator Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/translator-bot
ExecStart=/path/to/translator-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Jalankan:
```bash
sudo systemctl daemon-reload
sudo systemctl enable translator-bot
sudo systemctl start translator-bot
sudo systemctl status translator-bot
```

## 📝 Commands

- `/start` - Menu utama & pilih mode
- `/help` - Bantuan lengkap
- `/stats` - Lihat statistik bot

## ⚙️ Konfigurasi

Edit `config.py` atau `.env` untuk mengubah:

- `RATE_LIMIT_SECONDS` - Cooldown per user (default: 2 detik)
- `MAX_TEXT_LENGTH` - Max karakter per teks (default: 1000)
- `TRANSLATION_TIMEOUT` - Timeout translation (default: 10 detik)
- `LOG_LEVEL` - Level logging (INFO/DEBUG/WARNING)

## 🔧 Troubleshooting

### Bot tidak respond?

1. Cek token di `.env` sudah benar
2. Cek internet connection
3. Cek log: `tail -f logs/bot.log`

### Translation error?

1. Google Translate API mungkin down sementara
2. Teks terlalu panjang (> 1000 char)
3. Bahasa source tidak terdeteksi

### High memory usage?

1. Restart bot secara berkala
2. Turunkan `RATE_LIMIT_CLEANUP` di config
3. Monitor dengan `htop` atau `top`

## 📊 Monitoring

### Cek Logs

```bash
# Real-time
tail -f logs/bot.log

# Cari error
grep ERROR logs/bot.log

# 100 baris terakhir
tail -n 100 logs/bot.log
```

### Cek Stats

```bash
cat data/stats.json
```

## 🛡️ Security

- ✅ Environment variables untuk sensitive data
- ✅ Rate limiting untuk prevent spam
- ✅ Input validation
- ✅ Error handling comprehensive
- ✅ No hardcoded credentials

## 📈 Resource Usage

- **RAM**: ~50-100MB (idle)
- **CPU**: <5% (average)
- **Disk**: <10MB + logs
- **Network**: Minimal

Cocok untuk VPS kecil (512MB RAM).

## 🔄 Update Bot

```bash
git pull  # jika pakai git
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart translator-bot  # jika pakai systemd
```

## 🤝 Support

Created by: **@FEE999888**

Jika ada bug atau request fitur, hubungi via Telegram.

## 📄 License

Free to use. Dilarang dijual ulang tanpa izin.

---

**Status**: ✅ Production Ready | 🚀 Lightweight | 🛡️ Anti-Crash
