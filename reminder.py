"""Pengingat H-1 kontrol/rawat jalan via Telegram bot.

Skrip ini dijalankan SEKALI SEHARI (mis. lewat Scheduled Task di PythonAnywhere).
Untuk setiap pasien yang pengukuran TERAKHIR-nya mencatat "Tanggal Kontrol
Berikutnya" = BESOK, sebuah pesan dikirim ke nomor Telegram Anda (bukan ke
pasien).

Konfigurasi (environment variable):
  TELEGRAM_BOT_TOKEN   token bot dari @BotFather
  TELEGRAM_CHAT_ID     chat ID Telegram ANDA (tujuan pengingat)
  DATABASE_PATH        (opsional) lokasi data.db, default sama dengan aplikasi

Penggunaan:
  python reminder.py            # kirim pengingat untuk kontrol besok
  python reminder.py --dry-run  # tampilkan saja, tidak mengirim
  python reminder.py --test     # kirim 1 pesan uji ke Telegram Anda
  python reminder.py --date 2026-07-01   # uji untuk tanggal kontrol tertentu
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import timedelta

import db
import waktu
from config import Config

# Agar emoji/teks Indonesia bisa dicetak walau konsol non-UTF8 (mis. Windows).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def kirim_telegram(teks: str) -> bool:
    token = Config.TELEGRAM_BOT_TOKEN
    chat_id = Config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID belum diatur.")
        return False
    url = TELEGRAM_API.format(token=token)
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": teks,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=payload, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if not body.get("ok"):
                print("Telegram menolak:", body)
                return False
            return True
    except Exception as e:  # noqa: BLE001
        print("Gagal mengirim ke Telegram:", e)
        return False


def pesan_pengingat(row, tgl_kontrol) -> str:
    nama = row["nama"] or "(tanpa nama)"
    norm = row["no_rm"] or "-"
    return (
        "🔔 <b>Pengingat Kontrol H-1</b>\n"
        "Pasien dijadwalkan kontrol/rawat jalan <b>BESOK</b>.\n\n"
        "👤 Nama: <b>{nama}</b>\n"
        "🆔 No. RM: <b>{norm}</b>\n"
        "📅 Tanggal kontrol: <b>{tgl}</b>"
    ).format(nama=nama, norm=norm, tgl=tgl_kontrol)


def jalankan(target_tanggal: str, dry_run: bool = False) -> int:
    db.init_db()
    rows = db.pasien_kontrol_pada(target_tanggal)
    if not rows:
        print("Tidak ada pasien dengan kontrol pada", target_tanggal)
        return 0
    terkirim = 0
    for row in rows:
        teks = pesan_pengingat(row, target_tanggal)
        if dry_run:
            print("--- (dry-run) ---")
            print(teks)
            terkirim += 1
        elif kirim_telegram(teks):
            print("Terkirim: %s (No. RM %s)" % (row["nama"], row["no_rm"]))
            terkirim += 1
    print("Selesai. %d pengingat untuk kontrol %s." % (terkirim, target_tanggal))
    return terkirim


def main(argv):
    args = argv[1:]
    if "--test" in args:
        ok = kirim_telegram(
            "✅ Tes pengingat: bot Telegram terhubung. "
            "Pengingat kontrol H-1 siap digunakan."
        )
        print("Pesan uji terkirim." if ok else "Gagal mengirim pesan uji.")
        return 0 if ok else 1

    dry_run = "--dry-run" in args
    target = None
    if "--date" in args:
        target = args[args.index("--date") + 1]
    if target is None:
        # H-1: pengingat hari ini untuk kontrol BESOK (waktu lokal UTC+8).
        target = (waktu.hari_ini() + timedelta(days=1)).isoformat()

    jalankan(target, dry_run=dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
