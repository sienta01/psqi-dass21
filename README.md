# Form Pengambilan Data: Karakteristik Pasien + PSQI + DASS-21

Aplikasi web (Flask) untuk pengumpulan data penelitian: karakteristik pasien
stroke, penilaian kualitas tidur **PSQI**, dan tingkat depresi/cemas/stres
**DASS-21**. Skor dihitung **otomatis**, data tersimpan di database, dan dapat
**diekspor ke CSV** untuk analisis (Excel/SPSS). Seluruh antarmuka berbahasa
Indonesia.

---

## Fitur

- **Kuesioner 4 bagian** dengan tampilan bertahap (wizard): Data Pasien → PSQI → DASS-21 → MoCA-Ina.
- **Penghitungan skor otomatis**
  - PSQI: 7 komponen + skor global (0–21). Skor > 5 = kualitas tidur buruk.
  - DASS-21: subskala Depresi, Cemas, Stres (skor ×2) + kategori (Normal s/d Sangat Berat).
  - MoCA-Ina: rincian 7 domain kognitif + total (0–30) + interpretasi. Skor ≥ 26 = normal.
- **Desain longitudinal (2 kali ukur)** — tiap pasien diukur **Awal** (baseline)
  dan **Akhir**. Pengukuran akhir ditambah dari admin dengan memilih pasien dari
  daftar; data karakteristik tersalin otomatis dari baseline. Tersedia **halaman
  perbandingan Awal vs Akhir** lengkap dengan selisih (perubahan) tiap skor.
- **Validasi isian** di sisi browser dan server.
- **Halaman hasil** dengan rincian skor dan interpretasi (bisa dicetak/PDF).
- **Halaman admin** (dengan password) untuk melihat seluruh data dan **ekspor CSV**.
- Tanpa dependensi berat — hanya membutuhkan **Flask**. Database memakai SQLite bawaan Python.

---

## Struktur Berkas

```
psqi-dass21/
├── app.py                  # Aplikasi Flask (rute/halaman)
├── scoring.py              # Logika perhitungan PSQI, DASS-21 & MoCA-Ina
├── questions.py            # Seluruh pertanyaan & pilihan (Bahasa Indonesia)
├── db.py                   # Penyimpanan SQLite
├── export.py               # Ekspor data ke CSV
├── config.py               # Konfigurasi (password admin, secret key, dll)
├── requirements.txt        # Daftar dependensi (Flask)
├── wsgi_pythonanywhere.py  # Contoh file WSGI untuk PythonAnywhere
├── templates/              # Halaman HTML
├── static/                 # CSS & JavaScript
├── test_scoring.py         # Tes logika skor
└── test_app.py             # Tes alur aplikasi
```

---

## Menjalankan di Komputer Lokal (untuk uji coba)

1. Pasang Python 3.8+ lalu install Flask:
   ```bash
   pip install -r requirements.txt
   ```
2. Jalankan:
   ```bash
   python app.py
   ```
3. Buka `http://127.0.0.1:5000` di browser.
4. (Opsional) Jalankan tes:
   ```bash
   python test_scoring.py
   python test_app.py
   ```

---

## Cara Hosting di PythonAnywhere (Gratis)

> Akun gratis PythonAnywhere sudah cukup. Alamat aplikasi nanti berbentuk
> `https://USERNAME.pythonanywhere.com` dan otomatis memakai HTTPS.

### 1. Buat akun
Daftar di <https://www.pythonanywhere.com> (pilih paket **Beginner / gratis**).

### 2. Unggah berkas proyek
Ada dua cara — pilih salah satu:

**Cara A — Upload manual (paling mudah):**
1. Buka tab **Files**.
2. Buat folder baru bernama `psqi-dass21`.
3. Masuk ke folder itu, lalu unggah **semua berkas** proyek ini
   (app.py, scoring.py, questions.py, db.py, export.py, config.py,
   requirements.txt, serta folder `templates/` dan `static/` beserta isinya).

**Cara B — Lewat Git (jika proyek ada di GitHub):**
1. Buka tab **Consoles** → **Bash**.
2. Jalankan:
   ```bash
   git clone https://github.com/sienta01/psqi-dass21
   ```

### 3. Install Flask
Di tab **Consoles** → **Bash**, jalankan:
```bash
pip install --user Flask
```

### 4. Buat Web App
1. Buka tab **Web** → **Add a new web app** → **Next**.
2. Pilih **Manual configuration** (BUKAN "Flask" otomatis).
3. Pilih versi **Python 3.10** (atau yang tersedia, 3.8+).

### 5. Atur file WSGI
1. Masih di tab **Web**, cari bagian **Code** → klik tautan
   **WSGI configuration file** (mis. `/var/www/USERNAME_pythonanywhere_com_wsgi.py`).
2. **Hapus seluruh isinya**, lalu salin isi berkas
   [`wsgi_pythonanywhere.py`](wsgi_pythonanywhere.py) dari proyek ini.
3. Ganti `USERNAME` dengan username PythonAnywhere Anda.
4. **Ganti** `SECRET_KEY` dan `ADMIN_PASSWORD` dengan nilai rahasia Anda sendiri
   (lihat bagian Keamanan di bawah).
5. Simpan (**Save**).

### 6. (Opsional) Atur folder static
Agar CSS/JS termuat lebih cepat, di tab **Web** bagian **Static files** tambahkan:

| URL        | Directory                                   |
|------------|---------------------------------------------|
| `/static/` | `/home/USERNAME/psqi-dass21/static`         |

### 7. Reload
Klik tombol hijau besar **Reload** di tab **Web**. Buka
`https://USERNAME.pythonanywhere.com` — aplikasi siap dipakai.

---

## Keamanan (PENTING untuk Data Pasien)

Karena aplikasi menyimpan data pasien (termasuk identitas), lakukan hal berikut:

1. **Ganti `ADMIN_PASSWORD`** menjadi password yang kuat. Atur di file WSGI:
   ```python
   os.environ.setdefault("ADMIN_PASSWORD", "password-kuat-anda")
   ```
2. **Ganti `SECRET_KEY`** menjadi string acak panjang. Contoh membuatnya
   (jalankan di Bash console):
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Tempel hasilnya ke file WSGI pada `SECRET_KEY`.
3. Jangan bagikan tautan halaman `/admin` ke responden. Halaman pengisian
   untuk pasien cukup `https://USERNAME.pythonanywhere.com/isi`.
4. PythonAnywhere otomatis menyediakan **HTTPS**, jadi data terenkripsi saat dikirim.

---

## Cara Pakai

- **Untuk responden / petugas**: buka beranda → **Mulai Mengisi Kuesioner**,
  atau langsung ke `/isi`. Isi 4 bagian, lalu **Kirim** untuk melihat hasil.
  Hanya **Tanggal Pengambilan** dan **Nama Responden** yang wajib; bagian
  lain (termasuk MoCA-Ina) boleh dikosongkan.
- **Untuk peneliti (admin)**: klik **Admin** → masuk dengan password →
  lihat tabel **Data Pasien** (satu baris per pasien) → **Ekspor CSV** untuk analisis.
  Pada tiap baris tersedia **Detail**, **Edit** (skor dihitung ulang otomatis,
  data tidak diduplikasi), dan tombol **+ Akhir** / **Banding**.
  Menghapus pasien (dari halaman Detail) ikut menghapus pengukuran akhirnya.

### Alur pengukuran Awal & Akhir (longitudinal)

1. **Pengukuran awal (baseline)** diisi lewat halaman `/isi` seperti biasa →
   otomatis tercatat sebagai fase **Awal** dan membuat satu "pasien".
2. **Pengukuran akhir** — saat login sebagai **admin**, buka `/isi` lalu mulai
   mengetik nama di kolom **Nama Responden**. Pasien yang cocok akan muncul
   sebagai daftar; **pilih** salah satu (klik, atau navigasi dengan tombol
   **↑/↓** lalu **Enter**) → formulir berubah ke mode *Pengukuran Akhir*, data
   karakteristik **tersalin otomatis** dari baseline, dan Anda tinggal mengisi
   PSQI, DASS-21, dan MoCA-Ina. Menekan **Enter** saat tidak ada pasien yang
   cocok akan **lanjut sebagai pasien baru**. Alternatif: tombol **+ Akhir**
   pada tabel admin.
   > Catatan privasi: pencarian nama hanya muncul untuk admin yang login.
   > Pengunjung biasa di `/isi` hanya melihat kolom nama biasa.
3. Setelah tersimpan, buka **Banding** untuk melihat **perbandingan Awal vs
   Akhir** beserta selisih tiap skor (ditandai *membaik* / *memburuk*).
4. **Ekspor CSV** berisi kolom **Fase** (Awal/Akhir) dan **ID Pasien (Awal)**
   sehingga pasangan pengukuran tiap pasien mudah dianalisis (mis. uji
   berpasangan di SPSS).

---

## Catatan Teknis Skor

**PSQI** (Buysse dkk., 1989) — 7 komponen masing-masing 0–3:
1. Kualitas tidur subyektif (pertanyaan 9)
2. Latensi tidur (pertanyaan 2 + 5a)
3. Durasi tidur (pertanyaan 4)
4. Efisiensi tidur (pertanyaan 1, 3, 4)
5. Gangguan tidur (pertanyaan 5b–5j)
6. Penggunaan obat tidur (pertanyaan 6)
7. Disfungsi siang hari (pertanyaan 7 + 8)

Pertanyaan 10 & 11 dikumpulkan tetapi **tidak** masuk skor global (sesuai algoritma baku).

**DASS-21** — skor mentah tiap subskala (7 item, 0–3) **dikali 2**, lalu
diinterpretasi dengan ambang:

| Kategori     | Depresi | Cemas | Stres |
|--------------|---------|-------|-------|
| Normal       | 0–9     | 0–7   | 0–14  |
| Ringan       | 10–13   | 8–9   | 15–18 |
| Sedang       | 14–20   | 10–14 | 19–25 |
| Berat        | 21–27   | 15–19 | 26–33 |
| Sangat Berat | 28+     | 20+   | 34+   |

**MoCA-Ina** — skor dimasukkan per domain kognitif, dijumlahkan menjadi total
(maksimal 30):

| Domain | Skor maks |
|--------|-----------|
| Visuospasial / Eksekutif | 5 |
| Penamaan (Naming) | 3 |
| Atensi (Attention) | 6 |
| Bahasa (Language) | 3 |
| Abstraksi (Abstraction) | 2 |
| Memori / Recall Tertunda | 5 |
| Orientasi (Orientation) | 6 |

Penyesuaian pendidikan **+1** bila pendidikan formal ≤ 12 tahun (total tetap
maksimal 30). **Nilai potong: total ≥ 26 = fungsi kognitif normal**, di bawah
itu menandakan gangguan kognitif. Bila seluruh domain dikosongkan, MoCA-Ina
dicatat sebagai "tidak dinilai". Nilai potong & penyesuaian dapat diubah di
`scoring.py` (`MOCA_CUTOFF`).

---

## Penyesuaian

- **Mengubah teks pertanyaan/pilihan**: edit `questions.py`.
- **Mengubah aturan skor**: edit `scoring.py` (disertai tes di `test_scoring.py`).
- **Mengubah tampilan**: edit `static/style.css`.
- **Mengubah judul aplikasi**: atur `APP_TITLE` / `APP_SUBTITLE` di file WSGI
  atau `config.py`.
