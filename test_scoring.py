"""Tes cepat untuk logika scoring PSQI & DASS-21.

Jalankan: python test_scoring.py
"""
from scoring import hitung_psqi, hitung_dass21, jam_di_tempat_tidur


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


if __name__ == "__main__":
    test_jam_di_tempat_tidur()
    test_psqi_baik()
    test_psqi_buruk()
    test_dass_normal()
    test_dass_kategori()
    print("\nSemua tes lulus.")
