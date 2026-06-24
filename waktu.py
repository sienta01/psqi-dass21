"""Bantuan waktu lokal.

Server PythonAnywhere memakai UTC, sedangkan pengambilan data memakai waktu
lokal UTC+8 (mis. WITA). Seluruh tanggal/jam di aplikasi memakai zona ini agar
"hari ini", waktu input, dan pengingat sesuai waktu setempat.

Ubah ZONA bila perlu zona lain (mis. UTC+7 untuk WIB).
"""
from datetime import datetime, timezone, timedelta

ZONA = timezone(timedelta(hours=8))  # UTC+8


def sekarang():
    """Datetime sekarang di zona lokal (aware)."""
    return datetime.now(ZONA)


def hari_ini():
    """Objek date hari ini di zona lokal."""
    return sekarang().date()


def stempel_waktu():
    """Waktu input sebagai 'YYYY-MM-DDTHH:MM:SS' (tanpa offset, zona lokal)."""
    return sekarang().strftime("%Y-%m-%dT%H:%M:%S")
