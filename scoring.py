"""Logika penilaian (scoring) PSQI dan DASS-21.

Semua fungsi di sini murni (pure function): menerima dict jawaban mentah,
mengembalikan dict skor. Tidak menyentuh database / Flask, sehingga mudah diuji.
"""
from __future__ import annotations


# ----------------------------------------------------------------------------
# Util
# ----------------------------------------------------------------------------
def _to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _parse_time_to_minutes(value):
    """'HH:MM' -> menit sejak tengah malam. None jika tidak valid."""
    if not value:
        return None
    try:
        parts = str(value).split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return (h % 24) * 60 + (m % 60)
    except (ValueError, IndexError):
        return None


def jam_di_tempat_tidur(bedtime, waketime):
    """Selisih jam antara waktu bangun dan waktu berangkat tidur (jam, float)."""
    b = _parse_time_to_minutes(bedtime)
    w = _parse_time_to_minutes(waketime)
    if b is None or w is None:
        return None
    diff = w - b
    if diff <= 0:
        diff += 24 * 60  # lewat tengah malam
    return diff / 60.0


# ----------------------------------------------------------------------------
# PSQI  (Pittsburgh Sleep Quality Index)
# ----------------------------------------------------------------------------
# 7 komponen, masing-masing 0-3, total 0-21. Skor global > 5 = kualitas buruk.
#
# Pemetaan pertanyaan ke field jawaban (lihat questions.py):
#   q1  -> jam berangkat tidur (time)
#   q2  -> menit untuk tertidur (number)
#   q3  -> jam bangun pagi (time)
#   q4  -> jam tidur sebenarnya (number)
#   q5a..q5j -> frekuensi gangguan tidur (0-3)
#   q6  -> frekuensi minum obat tidur (0-3)
#   q7  -> frekuensi mengantuk di siang hari (0-3)
#   q8  -> kesulitan menjaga antusiasme (0-3)
#   q9  -> penilaian kualitas tidur keseluruhan (0-3)
# (q10 & q11a-e dikumpulkan tapi TIDAK masuk skor global, sesuai algoritma baku.)


def _komp2_latensi(menit, q5a):
    """Komponen 2: latensi tidur."""
    if menit is None:
        skor_q2 = 0
    elif menit <= 15:
        skor_q2 = 0
    elif menit <= 30:
        skor_q2 = 1
    elif menit <= 60:
        skor_q2 = 2
    else:
        skor_q2 = 3
    total = skor_q2 + _to_int(q5a)
    if total == 0:
        return 0
    if total <= 2:
        return 1
    if total <= 4:
        return 2
    return 3


def _komp3_durasi(jam):
    """Komponen 3: durasi tidur."""
    if jam is None:
        return 0
    if jam > 7:
        return 0
    if jam >= 6:
        return 1
    if jam >= 5:
        return 2
    return 3


def _komp4_efisiensi(jam_tidur, bedtime, waketime):
    """Komponen 4: efisiensi tidur = (jam tidur / jam di tempat tidur) x 100%."""
    jtt = jam_di_tempat_tidur(bedtime, waketime)
    if jam_tidur is None or jtt is None or jtt <= 0:
        return 0, None
    efisiensi = (jam_tidur / jtt) * 100.0
    if efisiensi >= 85:
        skor = 0
    elif efisiensi >= 75:
        skor = 1
    elif efisiensi >= 65:
        skor = 2
    else:
        skor = 3
    return skor, round(efisiensi, 1)


def _komp5_gangguan(ans):
    """Komponen 5: gangguan tidur = jumlah q5b..q5j (0-27) -> 0-3."""
    items = ["q5b", "q5c", "q5d", "q5e", "q5f", "q5g", "q5h", "q5i", "q5j"]
    total = sum(_to_int(ans.get("psqi_" + k)) for k in items)
    if total == 0:
        return 0
    if total <= 9:
        return 1
    if total <= 18:
        return 2
    return 3


def _komp7_disfungsi(q7, q8):
    """Komponen 7: disfungsi siang hari = q7 + q8 (0-6) -> 0-3."""
    total = _to_int(q7) + _to_int(q8)
    if total == 0:
        return 0
    if total <= 2:
        return 1
    if total <= 4:
        return 2
    return 3


def hitung_psqi(ans: dict) -> dict:
    """Hitung skor PSQI dari dict jawaban (key berawalan 'psqi_').

    Mengembalikan dict berisi 7 komponen, skor global, interpretasi,
    dan beberapa nilai bantu (efisiensi, jam di tempat tidur).
    """
    bedtime = ans.get("psqi_q1_bedtime")
    menit = _to_float(ans.get("psqi_q2_latency_min"))
    waketime = ans.get("psqi_q3_waketime")
    jam_tidur = _to_float(ans.get("psqi_q4_sleep_hours"))

    komp1 = _to_int(ans.get("psqi_q9"))                       # kualitas subyektif
    komp2 = _komp2_latensi(menit, ans.get("psqi_q5a"))        # latensi
    komp3 = _komp3_durasi(jam_tidur)                          # durasi
    komp4, efisiensi = _komp4_efisiensi(jam_tidur, bedtime, waketime)
    komp5 = _komp5_gangguan(ans)                              # gangguan tidur
    komp6 = _to_int(ans.get("psqi_q6"))                       # penggunaan obat
    komp7 = _komp7_disfungsi(ans.get("psqi_q7"), ans.get("psqi_q8"))

    global_score = komp1 + komp2 + komp3 + komp4 + komp5 + komp6 + komp7
    buruk = global_score > 5

    return {
        "komponen": {
            "k1_kualitas_subyektif": komp1,
            "k2_latensi_tidur": komp2,
            "k3_durasi_tidur": komp3,
            "k4_efisiensi_tidur": komp4,
            "k5_gangguan_tidur": komp5,
            "k6_penggunaan_obat": komp6,
            "k7_disfungsi_siang": komp7,
        },
        "efisiensi_persen": efisiensi,
        "jam_di_tempat_tidur": (
            round(jam_di_tempat_tidur(bedtime, waketime), 1)
            if jam_di_tempat_tidur(bedtime, waketime) is not None
            else None
        ),
        "skor_global": global_score,
        "interpretasi": (
            "Kualitas tidur buruk (indikasi gangguan tidur)"
            if buruk
            else "Kualitas tidur baik"
        ),
        "buruk": buruk,
    }


# Label komponen untuk ditampilkan / ekspor
PSQI_KOMPONEN_LABEL = {
    "k1_kualitas_subyektif": "Komponen 1 - Kualitas tidur subyektif",
    "k2_latensi_tidur": "Komponen 2 - Latensi tidur",
    "k3_durasi_tidur": "Komponen 3 - Durasi tidur",
    "k4_efisiensi_tidur": "Komponen 4 - Efisiensi tidur",
    "k5_gangguan_tidur": "Komponen 5 - Gangguan tidur",
    "k6_penggunaan_obat": "Komponen 6 - Penggunaan obat tidur",
    "k7_disfungsi_siang": "Komponen 7 - Disfungsi di siang hari",
}


# ----------------------------------------------------------------------------
# DASS-21  (Depression Anxiety Stress Scales - 21 item)
# ----------------------------------------------------------------------------
# Tiap subskala 7 item (0-3). Skor mentah dikali 2 agar setara DASS-42,
# lalu diinterpretasi dengan ambang baku.
DASS_SUBSKALA = {
    "depresi": [3, 5, 10, 13, 16, 17, 21],
    "cemas": [2, 4, 7, 9, 15, 19, 20],
    "stres": [1, 6, 8, 11, 12, 14, 18],
}

# Ambang interpretasi (berdasarkan skor x2), sesuai tabel pada formulir.
# Tuple: (batas_atas_inklusif, kategori)
_DASS_AMBANG = {
    "depresi": [(9, "Normal"), (13, "Ringan"), (20, "Sedang"), (27, "Berat"),
                (float("inf"), "Sangat Berat")],
    "cemas": [(7, "Normal"), (9, "Ringan"), (14, "Sedang"), (19, "Berat"),
              (float("inf"), "Sangat Berat")],
    "stres": [(14, "Normal"), (18, "Ringan"), (25, "Sedang"), (33, "Berat"),
              (float("inf"), "Sangat Berat")],
}


def _dass_kategori(subskala, skor):
    for batas, kategori in _DASS_AMBANG[subskala]:
        if skor <= batas:
            return kategori
    return "Sangat Berat"


def hitung_dass21(ans: dict) -> dict:
    """Hitung skor DASS-21 dari dict jawaban (key 'dass_q1'..'dass_q21')."""
    hasil = {}
    for subskala, items in DASS_SUBSKALA.items():
        mentah = sum(_to_int(ans.get(f"dass_q{i}")) for i in items)
        skor = mentah * 2
        hasil[subskala] = {
            "mentah": mentah,
            "skor": skor,
            "kategori": _dass_kategori(subskala, skor),
        }
    return hasil


DASS_SUBSKALA_LABEL = {
    "depresi": "Depresi",
    "cemas": "Cemas (Anxiety)",
    "stres": "Stres",
}


# ----------------------------------------------------------------------------
# MoCA-Ina  (Montreal Cognitive Assessment - versi Indonesia)
# ----------------------------------------------------------------------------
# 7 domain kognitif, total 30. Tambahan +1 bila pendidikan formal <= 12 tahun
# (maksimal tetap 30). Nilai potong baku: >= 26 = normal.
MOCA_DOMAIN_MAX = {
    "moca_visuospatial": 5,   # trail making, kubus, gambar jam
    "moca_naming": 3,         # menyebut 3 hewan
    "moca_attention": 6,      # rentang angka, kewaspadaan, serial 7
    "moca_language": 3,       # pengulangan kalimat, kelancaran verbal
    "moca_abstraction": 2,    # kemiripan dua benda
    "moca_recall": 5,         # recall tertunda 5 kata
    "moca_orientation": 6,    # tanggal, bulan, tahun, hari, tempat, kota
}
MOCA_TOTAL_MAX = 30
MOCA_CUTOFF = 26  # >= 26 dianggap normal


def _is_filled(value):
    return value is not None and str(value).strip() != ""


def _truthy(value):
    return str(value).strip().lower() not in ("", "0", "false", "no", "tidak")


def hitung_moca(ans: dict) -> dict:
    """Hitung skor MoCA-Ina per domain + total + interpretasi.

    Bila tidak ada satu pun domain yang diisi (dan tanpa penyesuaian
    pendidikan), MoCA dianggap TIDAK dinilai (`dinilai=False`).
    """
    domains = {}
    raw_sum = 0
    any_filled = False

    for name, maxv in MOCA_DOMAIN_MAX.items():
        if _is_filled(ans.get(name)):
            any_filled = True
        v = _to_int(ans.get(name))
        v = max(0, min(v, maxv))  # batasi 0..maks
        domains[name] = v
        raw_sum += v

    edu = _is_filled(ans.get("moca_edu_adjust")) and _truthy(ans.get("moca_edu_adjust"))
    if edu:
        any_filled = True

    if not any_filled:
        return {"dinilai": False}

    total = min(raw_sum + (1 if edu else 0), MOCA_TOTAL_MAX)
    normal = total >= MOCA_CUTOFF
    return {
        "dinilai": True,
        "domains": domains,
        "penyesuaian_pendidikan": 1 if edu else 0,
        "total": total,
        "normal": normal,
        "interpretasi": (
            "Fungsi kognitif normal"
            if normal
            else "Terdapat gangguan fungsi kognitif (di bawah nilai potong %d)"
            % MOCA_CUTOFF
        ),
    }


MOCA_DOMAIN_LABEL = {
    "moca_visuospatial": "Visuospasial / Eksekutif",
    "moca_naming": "Penamaan (Naming)",
    "moca_attention": "Atensi (Attention)",
    "moca_language": "Bahasa (Language)",
    "moca_abstraction": "Abstraksi (Abstraction)",
    "moca_recall": "Memori / Recall Tertunda",
    "moca_orientation": "Orientasi (Orientation)",
}


# ----------------------------------------------------------------------------
# Gabungan
# ----------------------------------------------------------------------------
def hitung_semua(ans: dict) -> dict:
    """Hitung PSQI + DASS-21 + MoCA-Ina sekaligus."""
    return {
        "psqi": hitung_psqi(ans),
        "dass21": hitung_dass21(ans),
        "moca": hitung_moca(ans),
    }


# ----------------------------------------------------------------------------
# Perbandingan dua pengukuran (Awal vs Akhir)
# ----------------------------------------------------------------------------
def _delta(awal, akhir):
    if awal is None or akhir is None:
        return None
    return akhir - awal


def _arah(delta, lebih_baik_bila_turun):
    """Tentukan apakah perubahan = membaik / memburuk / tetap.

    `lebih_baik_bila_turun`: True untuk PSQI & DASS (skor turun = membaik);
    False untuk MoCA (skor naik = membaik).
    """
    if delta is None or delta == 0:
        return "tetap"
    membaik = (delta < 0) if lebih_baik_bila_turun else (delta > 0)
    return "membaik" if membaik else "memburuk"


def bandingkan(awal: dict, akhir: dict) -> dict:
    """Bandingkan skor dua pengukuran. Mengembalikan selisih (akhir - awal)
    dan arah perubahan untuk PSQI, DASS-21, dan MoCA-Ina."""
    hasil = {}

    pa, pk = awal.get("psqi", {}), akhir.get("psqi", {})
    d = _delta(pa.get("skor_global"), pk.get("skor_global"))
    hasil["psqi"] = {
        "awal": pa.get("skor_global"), "akhir": pk.get("skor_global"),
        "delta": d, "arah": _arah(d, True),
        "awal_interpretasi": pa.get("interpretasi"),
        "akhir_interpretasi": pk.get("interpretasi"),
    }

    hasil["dass"] = {}
    for sub in ("depresi", "cemas", "stres"):
        da = awal.get("dass21", {}).get(sub, {})
        dk = akhir.get("dass21", {}).get(sub, {})
        d = _delta(da.get("skor"), dk.get("skor"))
        hasil["dass"][sub] = {
            "awal": da.get("skor"), "akhir": dk.get("skor"),
            "awal_kat": da.get("kategori"), "akhir_kat": dk.get("kategori"),
            "delta": d, "arah": _arah(d, True),
        }

    ma, mk = awal.get("moca", {}), akhir.get("moca", {})
    if ma.get("dinilai") and mk.get("dinilai"):
        d = _delta(ma.get("total"), mk.get("total"))
        domains = {}
        for key in MOCA_DOMAIN_MAX:
            va = ma.get("domains", {}).get(key)
            vk = mk.get("domains", {}).get(key)
            domains[key] = {"awal": va, "akhir": vk, "delta": _delta(va, vk)}
        hasil["moca"] = {
            "dinilai": True, "awal": ma.get("total"), "akhir": mk.get("total"),
            "delta": d, "arah": _arah(d, False), "domains": domains,
            "awal_interpretasi": ma.get("interpretasi"),
            "akhir_interpretasi": mk.get("interpretasi"),
        }
    else:
        hasil["moca"] = {"dinilai": False}

    return hasil
