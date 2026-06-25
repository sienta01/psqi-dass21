"""Konfigurasi aplikasi.

Sumber nilai (urutan prioritas):
  1. Environment variable (mis. diset di file WSGI untuk web app).
  2. File `secrets.json` di folder proyek (dibaca BAIK oleh web app MAUPUN
     skrip seperti reminder.py — cocok untuk token Telegram). Gitignored.
  3. Nilai default di bawah.

Contoh isi `secrets.json`:
  {
    "SECRET_KEY": "string-acak-panjang",
    "ADMIN_PASSWORD": "password-anda",
    "TELEGRAM_BOT_TOKEN": "123456789:ABCdef...",
    "TELEGRAM_CHAT_ID": "123456789"
  }
"""
import json
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Muat secrets.json bila ada (opsional). Tidak gagal bila tidak ada / rusak.
_SECRETS = {}
_secrets_path = os.path.join(BASE_DIR, "secrets.json")
if os.path.exists(_secrets_path):
    try:
        with open(_secrets_path, encoding="utf-8") as _f:
            _SECRETS = json.load(_f)
    except (ValueError, OSError):
        _SECRETS = {}


def _get(key, default=""):
    """Environment variable -> secrets.json -> default."""
    return os.environ.get(key) or _SECRETS.get(key) or default


class Config:
    # Kunci rahasia untuk session/cookie. WAJIB diganti saat produksi.
    SECRET_KEY = _get("SECRET_KEY", "ganti-kunci-rahasia-ini-saat-produksi")

    # Password untuk halaman admin (lihat data & ekspor). WAJIB diganti.
    ADMIN_PASSWORD = _get("ADMIN_PASSWORD", "admin123")

    # Lokasi file database SQLite.
    DATABASE_PATH = _get("DATABASE_PATH", os.path.join(BASE_DIR, "data.db"))

    # Nama institusi / judul yang tampil di header (opsional).
    APP_TITLE = _get("APP_TITLE", "Form Pengambilan Data Pasien")
    APP_SUBTITLE = _get(
        "APP_SUBTITLE", "Karakteristik Pasien • PSQI • DASS-21 • MoCA-Ina"
    )

    # Pengingat Telegram (lihat reminder.py & README).
    TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID", "")
