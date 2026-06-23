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
    data_json       TEXT NOT NULL,
    skor_json       TEXT NOT NULL
);
"""


def get_conn():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def simpan_response(data: dict, skor: dict) -> int:
    """Simpan satu respon. Mengembalikan id baris baru."""
    psqi = skor.get("psqi", {})
    dass = skor.get("dass21", {})
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
        json.dumps(data, ensure_ascii=False),
        json.dumps(skor, ensure_ascii=False),
    )
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO responses
               (created_at, tanggal, nama, no_rm, usia, jenis_kelamin,
                psqi_global, psqi_buruk, dass_depresi, dass_cemas, dass_stres,
                dass_depresi_kat, dass_cemas_kat, dass_stres_kat,
                data_json, skor_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        return cur.lastrowid


def update_response(resp_id: int, data: dict, skor: dict):
    """Perbarui satu respon yang sudah ada (skor dihitung ulang).

    `created_at` sengaja tidak diubah agar waktu input asli tetap tercatat.
    """
    psqi = skor.get("psqi", {})
    dass = skor.get("dass21", {})
    with get_conn() as conn:
        conn.execute(
            """UPDATE responses SET
               tanggal=?, nama=?, no_rm=?, usia=?, jenis_kelamin=?,
               psqi_global=?, psqi_buruk=?, dass_depresi=?, dass_cemas=?,
               dass_stres=?, dass_depresi_kat=?, dass_cemas_kat=?,
               dass_stres_kat=?, data_json=?, skor_json=?
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
    with get_conn() as conn:
        conn.execute("DELETE FROM responses WHERE id = ?", (resp_id,))


def hitung_total() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM responses").fetchone()["n"]
