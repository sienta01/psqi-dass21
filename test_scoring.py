"""Tes cepat untuk logika scoring PSQI & DASS-21.

Jalankan: python test_scoring.py
"""
from scoring import (
    hitung_psqi, hitung_dass21, hitung_moca, hitung_semua, bandingkan,
    jam_di_tempat_tidur,
)


def test_jam_di_tempat_tidur():
    assert jam_di_tempat_tidur("23:00", "06:00") == 7.0
    assert jam_di_tempat_tidur("22:30", "06:30") == 8.0
    assert jam_di_tempat_tidur("00:30", "08:00") == 7.5
    print("OK  jam_di_tempat_tidur")


def test_psqi_baik():
    # Responden tidur sangat baik -> skor global rendah
    ans = {
        "psqi_q1_bedtime": "22:00",
        "psqi_q2_latency_min": "10",   # komp2: q2=0
        "psqi_q3_waketime": "06:00",   # 8 jam di tempat tidur
        "psqi_q4_sleep_hours": "8",    # durasi >7 -> 0 ; efisiensi 100% -> 0
        "psqi_q5a": "0",
        "psqi_q6": "0",
        "psqi_q7": "0",
        "psqi_q8": "0",
        "psqi_q9": "0",
    }
    r = hitung_psqi(ans)
    assert r["skor_global"] == 0, r
    assert r["buruk"] is False
    assert r["efisiensi_persen"] == 100.0, r["efisiensi_persen"]
    print("OK  psqi baik (skor 0)")


def test_psqi_buruk():
    # Tidur buruk -> skor global tinggi (>5)
    ans = {
        "psqi_q1_bedtime": "01:00",
        "psqi_q2_latency_min": "75",   # >60 -> q2=3
        "psqi_q3_waketime": "05:00",   # 4 jam di tempat tidur
        "psqi_q4_sleep_hours": "3",    # durasi <5 -> 3 ; efisiensi 75% -> 1
        "psqi_q5a": "3",               # komp2: 3+3=6 -> 3
        "psqi_q5b": "3", "psqi_q5c": "3", "psqi_q5d": "2",
        "psqi_q6": "2",                # komp6 = 2
        "psqi_q7": "3", "psqi_q8": "3",  # komp7: 6 -> 3
        "psqi_q9": "3",                # komp1 = 3
    }
    r = hitung_psqi(ans)
    k = r["komponen"]
    assert k["k1_kualitas_subyektif"] == 3
    assert k["k2_latensi_tidur"] == 3
    assert k["k3_durasi_tidur"] == 3
    assert k["k4_efisiensi_tidur"] == 1, k["k4_efisiensi_tidur"]
    assert k["k6_penggunaan_obat"] == 2
    assert k["k7_disfungsi_siang"] == 3
    assert r["skor_global"] > 5
    assert r["buruk"] is True
    print("OK  psqi buruk (skor %d)" % r["skor_global"])


def test_dass_normal():
    ans = {f"dass_q{i}": "0" for i in range(1, 22)}
    r = hitung_dass21(ans)
    for sub in ("depresi", "cemas", "stres"):
        assert r[sub]["skor"] == 0
        assert r[sub]["kategori"] == "Normal"
    print("OK  dass normal (semua 0)")


def test_dass_kategori():
    # Semua item = 3 -> mentah 21 -> skor 42 -> Sangat Berat di semua subskala
    ans = {f"dass_q{i}": "3" for i in range(1, 22)}
    r = hitung_dass21(ans)
    for sub in ("depresi", "cemas", "stres"):
        assert r[sub]["mentah"] == 21
        assert r[sub]["skor"] == 42
        assert r[sub]["kategori"] == "Sangat Berat", (sub, r[sub])

    # Uji ambang batas depresi: mentah 5 -> skor 10 -> Ringan (10-13)
    ans = {f"dass_q{i}": "0" for i in range(1, 22)}
    # item depresi: 3,5,10,13,16 = 5 item bernilai 1 -> mentah 5
    for i in (3, 5, 10, 13, 16):
        ans[f"dass_q{i}"] = "1"
    r = hitung_dass21(ans)
    assert r["depresi"]["skor"] == 10
    assert r["depresi"]["kategori"] == "Ringan", r["depresi"]
    print("OK  dass kategori (ambang batas)")


def test_moca_normal():
    ans = {
        "moca_visuospatial": "5", "moca_naming": "3", "moca_attention": "6",
        "moca_language": "3", "moca_abstraction": "2", "moca_recall": "5",
        "moca_orientation": "6",
    }
    r = hitung_moca(ans)
    assert r["dinilai"] is True
    assert r["total"] == 30, r["total"]
    assert r["normal"] is True
    assert sum(r["domains"].values()) == 30
    print("OK  moca normal (total 30)")


def test_moca_impaired():
    ans = {
        "moca_visuospatial": "3", "moca_naming": "2", "moca_attention": "4",
        "moca_language": "2", "moca_abstraction": "1", "moca_recall": "2",
        "moca_orientation": "5",
    }
    r = hitung_moca(ans)
    assert r["total"] == 19, r["total"]
    assert r["normal"] is False
    print("OK  moca terganggu (total 19, < 26)")


def test_moca_edu_dan_cap():
    # Penyesuaian pendidikan +1
    r = hitung_moca({"moca_visuospatial": "5", "moca_orientation": "6",
                     "moca_edu_adjust": "1"})
    assert r["penyesuaian_pendidikan"] == 1
    assert r["total"] == 12, r["total"]  # 11 + 1
    # Cap di 30: semua maks + edu tetap 30
    full = {"moca_visuospatial": "5", "moca_naming": "3", "moca_attention": "6",
            "moca_language": "3", "moca_abstraction": "2", "moca_recall": "5",
            "moca_orientation": "6", "moca_edu_adjust": "1"}
    assert hitung_moca(full)["total"] == 30
    print("OK  moca penyesuaian pendidikan & cap 30")


def test_moca_tidak_dinilai():
    assert hitung_moca({})["dinilai"] is False
    assert hitung_moca({"moca_naming": "", "moca_recall": ""})["dinilai"] is False
    # Hanya centang edu tanpa domain -> tetap dianggap dinilai
    assert hitung_moca({"moca_edu_adjust": "1"})["dinilai"] is True
    print("OK  moca tidak dinilai (kosong) & deteksi terisi")


def test_moca_clamp():
    r = hitung_moca({"moca_naming": "9"})  # maks 3
    assert r["domains"]["moca_naming"] == 3
    assert r["total"] == 3
    print("OK  moca clamp nilai di atas maksimum")


def test_bandingkan():
    # Awal: tidur buruk, DASS tinggi, MoCA rendah
    awal = hitung_semua({
        "psqi_q9": "3", "psqi_q6": "2", "psqi_q7": "3", "psqi_q8": "3",
        "psqi_q4_sleep_hours": "3", "psqi_q2_latency_min": "75", "psqi_q5a": "3",
        **{f"dass_q{i}": "3" for i in range(1, 22)},
        "moca_visuospatial": "2", "moca_naming": "2", "moca_attention": "3",
        "moca_language": "2", "moca_abstraction": "1", "moca_recall": "2",
        "moca_orientation": "4",
    })
    # Akhir: membaik di semua instrumen
    akhir = hitung_semua({
        "psqi_q9": "0", "psqi_q6": "0", "psqi_q7": "0", "psqi_q8": "0",
        "psqi_q4_sleep_hours": "8", "psqi_q2_latency_min": "10", "psqi_q5a": "0",
        **{f"dass_q{i}": "0" for i in range(1, 22)},
        "moca_visuospatial": "5", "moca_naming": "3", "moca_attention": "6",
        "moca_language": "3", "moca_abstraction": "2", "moca_recall": "5",
        "moca_orientation": "6",
    })
    b = bandingkan(awal, akhir)
    # PSQI turun -> membaik
    assert b["psqi"]["delta"] < 0 and b["psqi"]["arah"] == "membaik"
    # DASS depresi turun -> membaik
    assert b["dass"]["depresi"]["delta"] < 0 and b["dass"]["depresi"]["arah"] == "membaik"
    # MoCA naik -> membaik (arah pakai logika naik=baik)
    assert b["moca"]["dinilai"] and b["moca"]["delta"] > 0
    assert b["moca"]["arah"] == "membaik"
    print("OK  bandingkan (deteksi membaik PSQI/DASS/MoCA)")


def test_bandingkan_moca_tidak_lengkap():
    awal = hitung_semua({"moca_naming": "2"})
    akhir = hitung_semua({})  # MoCA tidak dinilai
    b = bandingkan(awal, akhir)
    assert b["moca"]["dinilai"] is False
    print("OK  bandingkan moca tidak lengkap -> dinilai False")


if __name__ == "__main__":
    test_jam_di_tempat_tidur()
    test_psqi_baik()
    test_psqi_buruk()
    test_dass_normal()
    test_dass_kategori()
    test_moca_normal()
    test_moca_impaired()
    test_moca_edu_dan_cap()
    test_moca_tidak_dinilai()
    test_moca_clamp()
    test_bandingkan()
    test_bandingkan_moca_tidak_lengkap()
    print("\nSemua tes lulus.")
