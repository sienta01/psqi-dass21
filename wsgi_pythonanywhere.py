# ---------------------------------------------------------------------------
# Contoh file WSGI untuk PythonAnywhere.
#
# Di PythonAnywhere, buka tab "Web" -> bagian "Code" -> "WSGI configuration
# file". Ganti SELURUH isinya dengan kode di bawah ini, lalu sesuaikan:
#   - USERNAME       : ganti dengan username PythonAnywhere Anda
#   - nama folder    : sesuaikan jika folder proyek Anda berbeda
# Setelah itu klik tombol hijau "Reload".
# ---------------------------------------------------------------------------
import os
import sys

# 1) Arahkan ke folder proyek (tempat app.py berada).
USERNAME = "USERNAME"  # <-- GANTI dengan username PythonAnywhere Anda
project_home = "/home/{}/psqi-dass21".format(USERNAME)
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2) (Opsional tapi DISARANKAN) set konfigurasi rahasia di sini.
os.environ.setdefault("SECRET_KEY", "GANTI-DENGAN-STRING-ACAK-PANJANG")
os.environ.setdefault("ADMIN_PASSWORD", "GANTI-PASSWORD-ADMIN-ANDA")
# os.environ.setdefault("APP_TITLE", "Penelitian Tidur Pasien Stroke")

# 3) Impor objek Flask `app` sebagai `application` (WAJIB bernama application).
from app import app as application  # noqa: E402
