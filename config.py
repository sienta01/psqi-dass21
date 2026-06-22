"""Konfigurasi aplikasi.

Nilai-nilai penting (SECRET_KEY dan ADMIN_PASSWORD) sebaiknya diisi melalui
environment variable saat di-deploy di PythonAnywhere. Lihat README.md.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Kunci rahasia untuk session/cookie. WAJIB diganti saat produksi.
    SECRET_KEY = os.environ.get("SECRET_KEY", "ganti-kunci-rahasia-ini-saat-produksi")

    # Password untuk halaman admin (lihat data & ekspor). WAJIB diganti.
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

    # Lokasi file database SQLite.
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "data.db")
    )

    # Nama institusi / judul yang tampil di header (opsional).
    APP_TITLE = os.environ.get("APP_TITLE", "Form Pengambilan Data Pasien")
    APP_SUBTITLE = os.environ.get(
        "APP_SUBTITLE", "Karakteristik Pasien • PSQI • DASS-21"
    )
