"""Smoke test alur aplikasi memakai Flask test client.

Jalankan: python test_app.py
"""
import os
import tempfile

# Pakai DB sementara agar tidak mengotori data.db
os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "test_psqi.db")
os.environ["ADMIN_PASSWORD"] = "rahasia123"
if os.path.exists(os.environ["DATABASE_PATH"]):
    os.remove(os.environ["DATABASE_PATH"])

from app import app, EXPECTED_FIELDS, REQUIRED_FIELDS  # noqa: E402

app.config["TESTING"] = True


def isi_lengkap():
    """Bangun payload form yang valid & lengkap."""
    data = {name: "" for name in EXPECTED_FIELDS}
    data.update({
        "tanggal": "2026-06-22", "nama": "Budi Santoso", "no_rm": "RM123",
        "no_telp": "0812", "usia": "55", "jenis_kelamin": "Laki-laki",
        "pendidikan": "SMA", "pekerjaan": "Petani",
        "jenis_stroke": "Stroke Iskemik", "nihss": "Sedang (skor 5-15)",
        "lokasi_lesi": "Subkorteks", "lokasi_lesi_sisi": "Kanan",
        "intervensi": "Tidak", "stroke_berulang": "Tidak",
        "psqi_q1_bedtime": "23:00", "psqi_q2_latency_min": "20",
        "psqi_q3_waketime": "05:00", "psqi_q4_sleep_hours": "5",
        "psqi_q6": "1", "psqi_q7": "1", "psqi_q8": "2", "psqi_q9": "2",
    })
    for h in "abcdefghij":
        data["psqi_q5" + h] = "1"
    for i in range(1, 22):
        data["dass_q" + str(i)] = "2"
    return data


def main():
    client = app.test_client()

    # 1) Beranda
    r = client.get("/")
    assert r.status_code == 200, r.status_code
    print("OK  GET /")

    # 2) Halaman form + ambil csrf token dari session
    r = client.get("/isi")
    assert r.status_code == 200
    assert "DASS-21".encode() in r.data
    print("OK  GET /isi")

    # 3) Submit tidak lengkap -> kembali ke form (200) tanpa redirect
    with client.session_transaction() as s:
        token = s["_csrf"]
    r = client.post("/isi", data={"_csrf": token, "nama": "X"})
    assert r.status_code == 200
    assert b"belum lengkap" in r.data
    print("OK  POST /isi (validasi gagal ditangani)")

    # 4) Submit lengkap -> redirect ke /hasil/<id>
    payload = isi_lengkap()
    payload["_csrf"] = token
    r = client.post("/isi", data=payload)
    assert r.status_code == 302, r.status_code
    loc = r.headers["Location"]
    assert "/hasil/" in loc, loc
    print("OK  POST /isi lengkap -> redirect", loc)

    # 5) Halaman hasil menampilkan skor
    r = client.get(loc)
    assert r.status_code == 200
    body = r.data.decode()
    assert "PSQI" in body and "DASS-21" in body
    # DASS semua item = 2 -> mentah 14 -> skor 28 untuk tiap subskala
    assert "28" in body
    print("OK  GET /hasil menampilkan skor")

    # 6) Admin diproteksi
    r = client.get("/admin")
    assert r.status_code == 302 and "/admin/login" in r.headers["Location"]
    print("OK  /admin diproteksi (redirect login)")

    # 7) Login admin
    with client.session_transaction() as s:
        token = s["_csrf"]
    r = client.post("/admin/login", data={"_csrf": token, "password": "rahasia123"})
    assert r.status_code == 302
    r = client.get("/admin")
    assert r.status_code == 200 and b"Budi Santoso" in r.data
    print("OK  login admin & lihat data")

    # 8) Ekspor CSV
    r = client.get("/admin/export.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    csv_text = r.data.decode("utf-8")
    assert "Budi Santoso" in csv_text
    assert "PSQI Skor Global" in csv_text
    assert "DASS Depresi (skor x2)" in csv_text
    n_kolom = csv_text.splitlines()[0].count(",") + 1
    print("OK  ekspor CSV (%d kolom)" % n_kolom)

    print("\nSemua smoke test lulus.")


if __name__ == "__main__":
    main()
