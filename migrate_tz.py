"""Geser kolom `created_at` dari UTC ke UTC+8 (+8 jam) untuk data LAMA.

Hanya `created_at` (waktu input otomatis) yang dulu memakai UTC. Tanggal yang
Anda isi manual (tanggal pengambilan, tanggal kontrol) TIDAK diubah.

JALANKAN SEKALI SAJA. Bila dijalankan dua kali, waktu akan bergeser 16 jam.

Contoh:
  python migrate_tz.py --dry-run
      # tampilkan perubahan, TIDAK menulis ke database

  python migrate_tz.py --apply
      # geser SEMUA record +8 jam

  python migrate_tz.py --apply --before 2026-06-24T14:00:00
      # hanya record yang dibuat sebelum waktu (UTC) tsb. Gunakan ini bila
      # sudah ada record BARU yang terlanjur tersimpan dengan UTC+8.

DISARANKAN backup dulu:
  cp data.db data.db.bak        (Linux/PythonAnywhere)
"""
import argparse
import sqlite3
from datetime import datetime, timedelta

from config import Config


def main():
    ap = argparse.ArgumentParser(description="Geser created_at UTC -> UTC+8.")
    ap.add_argument("--apply", action="store_true", help="tulis perubahan")
    ap.add_argument("--dry-run", action="store_true", help="pratinjau saja")
    ap.add_argument("--before", help="hanya geser created_at < nilai ISO ini")
    ap.add_argument("--hours", type=int, default=8, help="jumlah jam (default 8)")
    args = ap.parse_args()

    if not args.apply and not args.dry_run:
        print("Tentukan --dry-run (pratinjau) atau --apply (tulis).")
        return

    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, created_at FROM responses ORDER BY id"
    ).fetchall()

    n = 0
    for r in rows:
        old = r["created_at"]
        if not old:
            continue
        if args.before and old >= args.before:
            continue
        try:
            dt = datetime.strptime(old[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            print("Lewati id %s (format tak dikenal): %s" % (r["id"], old))
            continue
        new = (dt + timedelta(hours=args.hours)).strftime("%Y-%m-%dT%H:%M:%S")
        print("id %-4s  %s  ->  %s" % (r["id"], old, new))
        if args.apply:
            conn.execute("UPDATE responses SET created_at=? WHERE id=?",
                         (new, r["id"]))
        n += 1

    if args.apply:
        conn.commit()
        print("\nSelesai: %d record digeser +%d jam." % (n, args.hours))
    else:
        print("\n(dry-run) %d record AKAN digeser +%d jam. "
              "Jalankan ulang dengan --apply untuk menerapkan." % (n, args.hours))
    conn.close()


if __name__ == "__main__":
    main()
