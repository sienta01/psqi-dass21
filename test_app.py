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
    # MoCA-Ina: total 5+3+6+3+2+5+6 = 30
    data.update({
        "moca_visuospatial": "5", "moca_naming": "3", "moca_attention": "6",
        "moca_language": "3", "moca_abstraction": "2", "moca_recall": "5",
        "moca_orientation": "6",
    })
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
    assert "PSQI" in body and "DASS-21" in body and "MoCA-Ina" in body
    # DASS semua item = 2 -> mentah 14 -> skor 28 untuk tiap subskala
    assert "28" in body
    # MoCA total 30 -> Fungsi kognitif normal
    assert "Fungsi kognitif normal" in body
    print("OK  GET /hasil menampilkan skor (PSQI, DASS, MoCA)")

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
    assert "MoCA Total" in csv_text and "MoCA Visuospasial / Eksekutif (maks 5)" in csv_text
    n_kolom = csv_text.splitlines()[0].count(",") + 1
    print("OK  ekspor CSV (%d kolom)" % n_kolom)

    # 9) Edit data responden #1: ganti nama & ubah semua DASS jadi 0
    r = client.get("/admin/edit/1")
    assert r.status_code == 200
    assert b"Mode edit" in r.data and b"Budi Santoso" in r.data
    print("OK  GET /admin/edit/1 (form ter-prefill)")

    with client.session_transaction() as s:
        token = s["_csrf"]
    payload = isi_lengkap()
    payload["nama"] = "Budi Diedit"
    payload["psqi_q4_sleep_hours"] = "8"      # ubah agar skor PSQI berubah
    for i in range(1, 22):
        payload["dass_q" + str(i)] = "0"       # semua Normal
    payload["_csrf"] = token
    r = client.post("/admin/edit/1", data=payload)
    assert r.status_code == 302 and "/admin/detail/1" in r.headers["Location"], r.headers.get("Location")

    r = client.get("/admin/detail/1")
    body = r.data.decode()
    assert "Budi Diedit" in body, "nama tidak terupdate"
    assert "Normal" in body, "kategori DASS tidak dihitung ulang"
    print("OK  POST /admin/edit/1 (data & skor ter-update)")

    # Pastikan tidak menambah baris baru (tetap 1 responden)
    r = client.get("/admin/export.csv")
    csv_text = r.data.decode("utf-8")
    assert "Budi Diedit" in csv_text and "Budi Santoso" not in csv_text
    assert len([ln for ln in csv_text.splitlines() if ln.strip()]) == 2  # header + 1 data
    print("OK  edit tidak menambah baris baru")

    # 11) Hanya Tanggal + Nama yang wajib: isian minimal harus diterima
    with client.session_transaction() as s:
        token = s["_csrf"]
    r = client.post("/isi", data={
        "_csrf": token, "tanggal": "2026-06-23", "nama": "Minimal Saja"})
    assert r.status_code == 302 and "/hasil/" in r.headers["Location"], r.status_code
    # Field opsional yang kosong dianggap 0 -> PSQI baik, DASS Normal
    r = client.get(r.headers["Location"])
    assert b"Kualitas tidur baik" in r.data and b"Normal" in r.data
    print("OK  POST /isi minimal (hanya tanggal+nama) diterima")

    # 12) Alur longitudinal: pengukuran awal -> akhir -> perbandingan
    with client.session_transaction() as s:
        token = s["_csrf"]
    awal = isi_lengkap()
    awal["nama"] = "Pasien Longitudinal"
    awal["psqi_q4_sleep_hours"] = "3"  # tidur buruk di awal
    awal["_csrf"] = token
    r = client.post("/isi", data=awal)
    pid = int(r.headers["Location"].rstrip("/").split("/")[-1])

    # Halaman tambah pengukuran akhir: demografi ter-prefill
    r = client.get("/admin/pasien/%d/akhir" % pid)
    assert r.status_code == 200
    assert b"Pengukuran Akhir" in r.data and b"Pasien Longitudinal" in r.data
    print("OK  GET /admin/pasien/<id>/akhir (demografi tersalin)")

    # Simpan pengukuran akhir (membaik)
    akhir = isi_lengkap()
    akhir["nama"] = "Pasien Longitudinal"
    akhir["psqi_q4_sleep_hours"] = "8"
    for i in range(1, 22):
        akhir["dass_q" + str(i)] = "0"
    akhir["_csrf"] = token
    r = client.post("/admin/pasien/%d/akhir" % pid, data=akhir)
    assert r.status_code == 302 and ("/admin/banding/%d" % pid) in r.headers["Location"]
    print("OK  POST pengukuran akhir -> redirect perbandingan")

    # Halaman perbandingan menampilkan selisih
    r = client.get("/admin/banding/%d" % pid)
    body = r.data.decode()
    assert "Perbandingan Awal vs Akhir" in body
    assert "membaik" in body  # minimal satu perubahan membaik
    print("OK  GET /admin/banding menampilkan selisih")

    # Tidak boleh menambah akhir kedua
    r = client.get("/admin/pasien/%d/akhir" % pid)
    assert r.status_code == 302 and ("/admin/banding/%d" % pid) in r.headers["Location"]
    print("OK  pengukuran akhir kedua ditolak")

    # Daftar admin: pasien ini berstatus 'Selesai'
    r = client.get("/admin")
    assert b"Selesai" in r.data
    print("OK  daftar admin menandai pasien selesai")

    # Ekspor: ada kolom Fase, dan dua baris (awal+akhir) berbagi ID Pasien
    r = client.get("/admin/export.csv")
    csv_text = r.data.decode("utf-8")
    assert "Fase" in csv_text and "ID Pasien (Awal)" in csv_text
    longis = [ln for ln in csv_text.splitlines() if "Pasien Longitudinal" in ln]
    assert len(longis) == 2, "harus 2 baris (awal & akhir)"
    print("OK  ekspor punya kolom Fase & pasangan awal+akhir")

    # Hapus pasien menghapus pengukuran akhir juga (cascade)
    r = client.post("/admin/hapus/%d" % pid, data={"_csrf": token})
    assert r.status_code == 302
    assert client.get("/admin/banding/%d" % pid).status_code == 404  # pasien hilang
    csv_text = client.get("/admin/export.csv").data.decode("utf-8")
    assert "Pasien Longitudinal" not in csv_text  # awal & akhir ikut terhapus
    print("OK  hapus pasien cascade ke pengukuran akhir")

    # 13) Alur autolengkap nama -> pengukuran akhir (admin)
    # Budi (#1) adalah pengukuran awal tanpa akhir.
    r = client.get("/admin/cari-pasien?q=Budi")
    hits = r.get_json()
    assert r.status_code == 200 and any(h["id"] == 1 for h in hits), hits
    print("OK  GET /admin/cari-pasien menemukan pasien")

    r = client.get("/admin/pasien/1/data")
    js = r.get_json()
    assert "Budi" in (js["nama"] or "") and js["demografi"]["jenis_stroke"]
    print("OK  GET /admin/pasien/1/data mengembalikan demografi")

    with client.session_transaction() as s:
        token = s["_csrf"]
    akhir = isi_lengkap()
    akhir["nama"] = "Budi Diedit"
    akhir["parent_id"] = "1"           # tautkan sebagai pengukuran akhir Budi
    akhir["_csrf"] = token
    r = client.post("/isi", data=akhir)
    assert r.status_code == 302 and "/admin/banding/1" in r.headers["Location"], r.headers.get("Location")
    assert client.get("/admin/banding/1").status_code == 200
    print("OK  POST /isi dengan parent_id -> tersimpan sebagai akhir")

    # Non-admin tidak boleh menautkan akhir (parent_id diabaikan)
    client.get("/admin/logout")
    client.get("/isi")
    with client.session_transaction() as s:
        token = s["_csrf"]
    r = client.post("/isi", data={
        "_csrf": token, "tanggal": "2026-06-23", "nama": "Penyusup",
        "parent_id": "2"})
    assert r.status_code == 302 and "/hasil/" in r.headers["Location"], r.headers.get("Location")
    print("OK  non-admin: parent_id diabaikan (tetap pengukuran awal)")

    print("\nSemua smoke test lulus.")


if __name__ == "__main__":
    main()
