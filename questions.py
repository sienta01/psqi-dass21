"""Definisi seluruh pertanyaan & pilihan dalam Bahasa Indonesia.

Dipakai oleh template (render form) dan modul ekspor (label kolom).
Sumber: "Form Pengambilan Data" (Karakteristik Pasien, PSQI, DASS-21).
"""

# ---------------------------------------------------------------------------
# 1) FORMULIR KARAKTERISTIK PASIEN
# ---------------------------------------------------------------------------
# type: text | date | number | tel | radio | radio_other
PASIEN_FIELDS = [
    {"name": "tanggal", "label": "Tanggal Pengambilan", "type": "date", "required": True},
    {"name": "nama", "label": "Nama Responden", "type": "text", "required": True},
    {"name": "no_rm", "label": "Nomor Rekam Medis", "type": "text", "required": False},
    {"name": "no_telp", "label": "Nomor Telepon", "type": "tel", "required": False},
    {"name": "usia", "label": "Usia (tahun)", "type": "number", "required": False,
     "min": 0, "max": 120},
    {"name": "jenis_kelamin", "label": "Jenis Kelamin", "type": "radio", "required": False,
     "options": ["Laki-laki", "Perempuan"]},
    {"name": "pendidikan", "label": "Pendidikan Terakhir", "type": "radio", "required": False,
     "options": ["SD", "SMP", "SMA", "Sarjana", "Tidak sekolah"]},
    {"name": "pekerjaan", "label": "Pekerjaan", "type": "text", "required": False},
    {"name": "jenis_stroke", "label": "Jenis Stroke", "type": "radio", "required": False,
     "options": ["Stroke Iskemik", "Stroke Hemoragik"]},
    {"name": "nihss", "label": "NIHSS saat Admisi", "type": "radio", "required": False,
     "options": [
         "Minor (skor 1-4)",
         "Sedang (skor 5-15)",
         "Sedang-berat (skor 16-20)",
         "Berat (skor 21-42)",
     ]},
    {"name": "lokasi_lesi", "label": "Lokasi Lesi", "type": "radio", "required": False,
     "options": [
         "Korteks lobus frontal",
         "Korteks lobus parietal",
         "Korteks lobus temporal",
         "Korteks lobus oksipital",
         "Insula",
         "Subkorteks",
         "Batang otak",
         "Serebelum",
         "Subarachnoid",
     ]},
    {"name": "lokasi_lesi_sisi", "label": "Lokasi Lesi (Kanan/Kiri)", "type": "radio",
     "required": False, "options": ["Kanan", "Kiri"]},
    {"name": "intervensi", "label": "Tindakan Intervensi atau Operatif",
     "type": "radio_other", "required": False, "options": ["Ya", "Tidak"],
     "other_value": "Ya", "other_name": "intervensi_ket",
     "other_label": "Sebutkan tindakan"},
    {"name": "stroke_berulang", "label": "Riwayat Stroke Berulang", "type": "radio",
     "required": False, "options": ["Ya", "Tidak"]},
    {"name": "cogstim_explained", "label": "Edukasi Cognitive Stimulation (cogstim)",
     "type": "checkbox", "required": False,
     "checkbox_text": "Sudah dijelaskan kepada pasien/keluarga"},
    {"name": "kontrol_berikutnya",
     "label": "Tanggal Kontrol / Rawat Jalan Berikutnya",
     "type": "date", "required": False,
     "hint": "Dipakai untuk pengingat H-1 via Telegram."},
]

# Field demografi yang TIDAK disalin saat menambah pengukuran lanjutan
# (diisi ulang tiap kunjungan).
FIELDS_TIDAK_DISALIN = {"tanggal", "kontrol_berikutnya"}


# ---------------------------------------------------------------------------
# 2) PSQI
# ---------------------------------------------------------------------------
PSQI_PETUNJUK = (
    "Pertanyaan berikut berhubungan dengan kebiasaan tidur Anda selama "
    "SEBULAN TERAKHIR. Jawaban Anda harus menggambarkan keadaan Anda pada "
    "sebagian besar siang dan malam selama sebulan terakhir. Mohon jawab "
    "semua pertanyaan."
)

# Skala frekuensi umum (q5*, q6, q7)
PSQI_SKALA_FREKUENSI = [
    (0, "Tidak pernah selama sebulan terakhir"),
    (1, "Kurang dari sekali seminggu"),
    (2, "Sekali atau dua kali seminggu"),
    (3, "Tiga kali atau lebih dalam seminggu"),
]

# Pertanyaan 1-4 (isian)
PSQI_ISIAN = [
    {"name": "psqi_q1_bedtime", "no": "1",
     "label": "Jam berapa Anda biasanya mulai tidur malam?", "type": "time"},
    {"name": "psqi_q2_latency_min", "no": "2",
     "label": "Berapa lama (dalam menit) yang Anda butuhkan untuk tertidur "
              "setiap malam?", "type": "number", "min": 0, "max": 600,
     "suffix": "menit"},
    {"name": "psqi_q3_waketime", "no": "3",
     "label": "Jam berapa Anda biasanya bangun pagi?", "type": "time"},
    {"name": "psqi_q4_sleep_hours", "no": "4",
     "label": "Berapa jam Anda benar-benar tidur di malam hari? "
              "(bisa berbeda dengan lama Anda berada di tempat tidur)",
     "type": "number", "min": 0, "max": 24, "step": "0.5", "suffix": "jam"},
]

# Pertanyaan 5: sub a-j (skala frekuensi)
PSQI_Q5_ITEMS = [
    ("psqi_q5a", "a", "Tidak bisa tertidur dalam waktu 30 menit"),
    ("psqi_q5b", "b", "Terbangun di tengah malam atau dini hari"),
    ("psqi_q5c", "c", "Harus bangun untuk ke kamar mandi"),
    ("psqi_q5d", "d", "Tidak bisa bernapas dengan nyaman"),
    ("psqi_q5e", "e", "Batuk atau mendengkur keras"),
    ("psqi_q5f", "f", "Merasa kedinginan"),
    ("psqi_q5g", "g", "Merasa kepanasan"),
    ("psqi_q5h", "h", "Mengalami mimpi buruk"),
    ("psqi_q5i", "i", "Merasakan nyeri"),
    ("psqi_q5j", "j", "Alasan lain (jika ada)"),
]
PSQI_Q5J_OTHER = "psqi_q5j_text"  # keterangan alasan lain

# Pertanyaan 6 & 7 (skala frekuensi)
PSQI_Q6 = {
    "name": "psqi_q6", "no": "6",
    "label": "Seberapa sering Anda minum obat agar bisa tidur "
             "(obat resep maupun obat bebas)?",
}
PSQI_Q7 = {
    "name": "psqi_q7", "no": "7",
    "label": "Seberapa sering Anda mengalami kesulitan menjaga diri tetap "
             "terjaga (tidak mengantuk) saat mengemudi, makan, atau "
             "beraktivitas sosial?",
}

# Pertanyaan 8 (skala kesulitan)
PSQI_Q8 = {
    "name": "psqi_q8", "no": "8",
    "label": "Seberapa sulit bagi Anda untuk tetap antusias menyelesaikan "
             "berbagai hal?",
    "skala": [
        (0, "Tidak sulit sama sekali"),
        (1, "Sedikit sulit"),
        (2, "Lumayan sulit"),
        (3, "Sangat sulit"),
    ],
}

# Pertanyaan 9 (kualitas keseluruhan)
PSQI_Q9 = {
    "name": "psqi_q9", "no": "9",
    "label": "Bagaimana Anda menilai kualitas tidur Anda secara keseluruhan?",
    "skala": [
        (0, "Sangat baik"),
        (1, "Cukup baik"),
        (2, "Agak buruk"),
        (3, "Sangat buruk"),
    ],
}

# Pertanyaan 10 (teman sekamar - tidak masuk skor)
PSQI_Q10 = {
    "name": "psqi_q10", "no": "10",
    "label": "Apakah Anda memiliki teman sekamar atau pasangan seranjang?",
    "catatan": "Tidak diperhitungkan dalam skor total.",
    "skala": [
        (0, "Tidak ada pasangan / teman sekamar"),
        (1, "Pasangan / teman sekamar di kamar lain"),
        (2, "Pasangan di kamar yang sama, tapi beda ranjang"),
        (3, "Pasangan di ranjang yang sama"),
    ],
}

# Pertanyaan 11 (laporan teman seranjang - tidak masuk skor)
PSQI_Q11_PENGANTAR = (
    "Bila Anda punya teman seranjang atau sekamar, tanyakan kepadanya "
    "seberapa sering selama sebulan terakhir Anda mengalami hal berikut "
    "(tidak diperhitungkan dalam skor total):"
)
PSQI_Q11_ITEMS = [
    ("psqi_q11a", "a", "Mendengkur keras"),
    ("psqi_q11b", "b", "Jeda panjang antar napas saat tidur"),
    ("psqi_q11c", "c", "Kaki berkedut atau menyentak saat tidur"),
    ("psqi_q11d", "d", "Episode disorientasi atau kebingungan saat tidur"),
    ("psqi_q11e", "e", "Kegelisahan lain saat tidur"),
]
PSQI_Q11E_OTHER = "psqi_q11e_text"


# ---------------------------------------------------------------------------
# 3) DASS-21
# ---------------------------------------------------------------------------
DASS_PETUNJUK = (
    "Bacalah setiap pernyataan dan pilih angka 0, 1, 2, atau 3 yang paling "
    "menggambarkan kondisi Anda selama SATU MINGGU TERAKHIR. Tidak ada "
    "jawaban benar atau salah. Jangan menghabiskan waktu terlalu lama untuk "
    "tiap pernyataan."
)
DASS_SKALA = [
    (0, "Tidak pernah", "Tidak pernah dialami"),
    (1, "Kadang", "Kadang dialami"),
    (2, "Sering", "Sering dialami"),
    (3, "Sangat sering", "Sangat sering dialami"),
]

# (nomor, kode subskala, teks). Kode: d=depresi, a=cemas, s=stres.
DASS_ITEMS = [
    (1, "s", "Saya merasa sulit untuk ditenangkan"),
    (2, "a", "Saya merasa mulut saya kering"),
    (3, "d", "Saya tidak dapat merasakan perasaan yang positif sama sekali"),
    (4, "a", "Saya mengalami kesulitan bernapas (misalnya napas cepat "
             "berlebihan, terengah-engah meski tidak melakukan aktivitas fisik)"),
    (5, "d", "Saya merasa sulit mendapatkan semangat untuk melakukan sesuatu"),
    (6, "s", "Saya cenderung bereaksi berlebihan terhadap suatu situasi"),
    (7, "a", "Saya mengalami gemetar (misalnya pada tangan)"),
    (8, "s", "Saya merasa banyak menghabiskan energi untuk merasa cemas"),
    (9, "a", "Saya merasa khawatir terhadap situasi di mana saya mungkin "
             "panik dan mempermalukan diri sendiri"),
    (10, "d", "Saya merasa tidak ada hal yang dapat saya harapkan (tidak "
              "punya harapan ke depan)"),
    (11, "s", "Saya merasa diri saya mudah gelisah"),
    (12, "s", "Saya merasa sulit untuk bersantai (rileks)"),
    (13, "d", "Saya merasa sedih dan murung"),
    (14, "s", "Saya merasa tidak sabar/tidak tahan terhadap hal yang "
              "menghalangi saya menyelesaikan apa yang sedang saya lakukan"),
    (15, "a", "Saya merasa hampir panik"),
    (16, "d", "Saya tidak merasa antusias terhadap hal apa pun"),
    (17, "d", "Saya merasa diri saya tidak berharga"),
    (18, "s", "Saya merasa mudah tersinggung"),
    (19, "a", "Saya menyadari kerja jantung saya tanpa melakukan aktivitas "
              "fisik (misalnya jantung berdebar atau terasa berhenti sejenak)"),
    (20, "a", "Saya merasa takut tanpa alasan yang jelas"),
    (21, "d", "Saya merasa hidup ini tidak berarti"),
]

# Ringkasan ambang interpretasi DASS-21 (untuk ditampilkan di halaman hasil)
DASS_TABEL_INTERPRETASI = {
    "header": ["Kategori", "Depresi", "Cemas", "Stres"],
    "rows": [
        ["Normal", "0-9", "0-7", "0-14"],
        ["Ringan", "10-13", "8-9", "15-18"],
        ["Sedang", "14-20", "10-14", "19-25"],
        ["Berat", "21-27", "15-19", "26-33"],
        ["Sangat Berat", "28+", "20+", "34+"],
    ],
}


# ---------------------------------------------------------------------------
# 4) MoCA-Ina (Montreal Cognitive Assessment - versi Indonesia)
# ---------------------------------------------------------------------------
MOCA_PETUNJUK = (
    "Masukkan skor MoCA-Ina untuk setiap domain kognitif sesuai hasil "
    "pemeriksaan. Total maksimal 30. Centang penyesuaian pendidikan bila "
    "pendidikan formal pasien ≤ 12 tahun (+1, maksimal tetap 30). "
    "Nilai potong: skor ≥ 26 dianggap normal. Bagian ini opsional — "
    "kosongkan bila MoCA tidak dinilai."
)

# (name, label, max, deskripsi sub-tugas)
MOCA_DOMAINS = [
    ("moca_visuospatial", "Visuospasial / Eksekutif", 5,
     "Alternating trail making, meniru kubus, menggambar jam"),
    ("moca_naming", "Penamaan (Naming)", 3,
     "Menyebutkan nama 3 hewan"),
    ("moca_attention", "Atensi (Attention)", 6,
     "Rentang angka (maju & mundur), kewaspadaan, pengurangan serial 7"),
    ("moca_language", "Bahasa (Language)", 3,
     "Pengulangan kalimat, kelancaran verbal (fonemik)"),
    ("moca_abstraction", "Abstraksi (Abstraction)", 2,
     "Kemiripan antara dua benda"),
    ("moca_recall", "Memori / Recall Tertunda", 5,
     "Mengingat kembali 5 kata setelah jeda (tanpa isyarat)"),
    ("moca_orientation", "Orientasi (Orientation)", 6,
     "Tanggal, bulan, tahun, hari, tempat, dan kota"),
]

MOCA_EDU_FIELD = "moca_edu_adjust"
MOCA_EDU_LABEL = "Penyesuaian pendidikan (+1, bila pendidikan formal ≤ 12 tahun)"
MOCA_TOTAL_MAX = 30
MOCA_CUTOFF = 26
