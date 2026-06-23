"""Lapisan database sederhana memakai sqlite3 (tanpa dependensi tambahan).

Satu tabel `responses`:
  - kolom datar untuk identifikasi & skor ringkas (memudahkan listing/filter)
  - kolom JSON `data_json`  : seluruh jawaban mentah
  - kolom JSON `skor_json`  : seluruh hasil perhitungan
"""
import json
import sqlite3
from datetime import datetime

from config import Config

SCHEMA = """
CREATE TABLE IF NOT EXISTS responses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL,
    tanggal         TEXT,
    nama            TEXT,
    no_rm           TEXT,
    usia            TEXT,
    jenis_kelamin   TEXT,
    psqi_global     INTEGER,
    psqi_buruk      INTEGER,
    dass_depresi    INTEGER,
    dass_cemas      INTEGER,
    dass_stres      INTEGER,
    dass_depresi_kat TEXT,
    dass_cemas_kat   TEXT,
    dass_stres_kat   TEXT,
    moca_total      INTEGER,
    fase            TEXT NOT NULL DEFAULT 'awal',
    parent_id       INTEGER,
    data_json       TEXT NOT NULL,
    skor_json       TEXT NOT NULL
);
"""

# Kolom yang mungkin perlu ditambahkan ke database lama (migrasi ringan).
MIGRATIONS = [
    ("moca_total", "INTEGER"),
    ("fase", "TEXT NOT NULL DEFAULT 'awal'"),
    ("parent_id", "INTEGER"),
]


def get_conn():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(responses)")}
        for col, decl in MIGRATIONS:
            if col not in existing:
                conn.execute(f"ALTER TABLE responses ADD COLUMN {col} {decl}")


def simpan_response(data: dict, skor: dict, fase: str = "awal",
                    parent_id: int = None) -> int:
    """Simpan satu pengukuran. `fase` = 'awal' atau 'akhir'; `parent_id`
    menunjuk ke pengukuran awal bila ini pengukuran akhir. Kembalikan id baru."""
    psqi = skor.get("psqi", {})
    dass = skor.get("dass21", {})
    moca = skor.get("moca", {})
    row = (
        datetime.now().isoformat(timespec="seconds"),
        data.get("tanggal"),
        data.get("nama"),
        data.get("no_rm"),
        data.get("usia"),
        data.get("jenis_kelamin"),
        psqi.get("skor_global"),
        1 if psqi.get("buruk") else 0,
        dass.get("depresi", {}).get("skor"),
        dass.get("cemas", {}).get("skor"),
        dass.get("stres", {}).get("skor"),
        dass.get("depresi", {}).get("kategori"),
        dass.get("cemas", {}).get("kategori"),
        dass.get("stres", {}).get("kategori"),
        moca.get("total") if moca.get("dinilai") else None,
        fase,
        parent_id,
        json.dumps(data, ensure_ascii=False),
        json.dumps(skor, ensure_ascii=False),
    )
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO responses
               (created_at, tanggal, nama, no_rm, usia, jenis_kelamin,
                psqi_global, psqi_buruk, dass_depresi, dass_cemas, dass_stres,
                dass_depresi_kat, dass_cemas_kat, dass_stres_kat,
                moca_total, fase, parent_id, data_json, skor_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        return cur.lastrowid


def update_response(resp_id: int, data: dict, skor: dict):
    """Perbarui satu respon yang sudah ada (skor dihitung ulang).

    `created_at` sengaja tidak diubah agar waktu input asli tetap tercatat.
    """
    psqi = skor.get("psqi", {})
    dass = skor.get("dass21", {})
    moca = skor.get("moca", {})
    with get_conn() as conn:
        conn.execute(
            """UPDATE responses SET
               tanggal=?, nama=?, no_rm=?, usia=?, jenis_kelamin=?,
               psqi_global=?, psqi_buruk=?, dass_depresi=?, dass_cemas=?,
               dass_stres=?, dass_depresi_kat=?, dass_cemas_kat=?,
               dass_stres_kat=?, moca_total=?, data_json=?, skor_json=?
               WHERE id=?""",
            (
                data.get("tanggal"), data.get("nama"), data.get("no_rm"),
                data.get("usia"), data.get("jenis_kelamin"),
                psqi.get("skor_global"), 1 if psqi.get("buruk") else 0,
                dass.get("depresi", {}).get("skor"),
                dass.get("cemas", {}).get("skor"),
                dass.get("stres", {}).get("skor"),
                dass.get("depresi", {}).get("kategori"),
                dass.get("cemas", {}).get("kategori"),
                dass.get("stres", {}).get("kategori"),
                moca.get("total") if moca.get("dinilai") else None,
                json.dumps(data, ensure_ascii=False),
                json.dumps(skor, ensure_ascii=False),
                resp_id,
            ),
        )


def ambil_semua(order_desc=True):
    arah = "DESC" if order_desc else "ASC"
    with get_conn() as conn:
        return conn.execute(
            f"SELECT * FROM responses ORDER BY id {arah}"
        ).fetchall()


def ambil_satu(resp_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM responses WHERE id = ?", (resp_id,)
        ).fetchone()


def hapus_satu(resp_id: int):
    """Hapus satu pengukuran. Bila ini pengukuran awal, pengukuran akhir
    miliknya ikut terhapus (cascade)."""
    with get_conn() as conn:
        conn.execute("DELETE FROM responses WHERE id = ? OR parent_id = ?",
                     (resp_id, resp_id))


def hitung_total() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM responses").fetchone()["n"]


# ---------------------------------------------------------------------------
# Query untuk desain longitudinal (pengukuran awal & akhir)
# ---------------------------------------------------------------------------
def ambil_pasien_list():
    """Satu baris per pasien (pengukuran awal), beserta ringkasan pengukuran
    akhir bila ada (LEFT JOIN)."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.*,
                      b.id          AS akhir_id,
                      b.tanggal     AS akhir_tanggal,
                      b.psqi_global AS akhir_psqi_global,
                      b.psqi_buruk  AS akhir_psqi_buruk,
                      b.dass_depresi AS akhir_dass_depresi,
                      b.dass_cemas  AS akhir_dass_cemas,
                      b.dass_stres  AS akhir_dass_stres,
                      b.moca_total  AS akhir_moca_total
               FROM responses a
               LEFT JOIN responses b
                      ON b.parent_id = a.id AND b.fase = 'akhir'
               WHERE a.fase = 'awal'
               ORDER BY a.id DESC""",
        ).fetchall()


def ambil_awal_tanpa_akhir():
    """Pengukuran awal yang BELUM punya pengukuran akhir (untuk pilihan)."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.* FROM responses a
               WHERE a.fase = 'awal'
                 AND NOT EXISTS (
                     SELECT 1 FROM responses b
                     WHERE b.parent_id = a.id AND b.fase = 'akhir')
               ORDER BY a.id DESC""",
        ).fetchall()


def ambil_akhir(parent_id: int):
    """Pengukuran akhir untuk satu pasien (atau None)."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM responses WHERE parent_id = ? AND fase = 'akhir'",
            (parent_id,),
        ).fetchone()


def cari_pasien(q: str, limit: int = 10):
    """Cari pengukuran AWAL yang BELUM punya akhir, berdasarkan nama / No. RM.
    Untuk fitur autolengkap saat menambah pengukuran akhir lewat form."""
    like = "%" + q + "%"
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.id, a.nama, a.no_rm, a.tanggal, a.usia
               FROM responses a
               WHERE a.fase = 'awal'
                 AND (a.nama LIKE ? OR IFNULL(a.no_rm,'') LIKE ?)
                 AND NOT EXISTS (
                     SELECT 1 FROM responses b
                     WHERE b.parent_id = a.id AND b.fase = 'akhir')
               ORDER BY a.nama
               LIMIT ?""",
            (like, like, limit),
        ).fetchall()
