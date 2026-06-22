"""Ekspor data respon ke CSV (lebar/flat) untuk analisis di Excel/SPSS.

Menghasilkan satu baris per responden dengan seluruh jawaban mentah dan skor.
CSV ditulis dengan BOM UTF-8 agar karakter Indonesia tampil benar di Excel.
"""
import csv
import io
import json

import questions as Q
from scoring import PSQI_KOMPONEN_LABEL


def _build_spec():
    """Daftar terurut (label_kolom, fungsi_ambil). fungsi_ambil(data, skor)->nilai."""
    spec = []

    def d(key):  # ambil dari data mentah
        return lambda data, skor, k=key: data.get(k, "")

    # Metadata
    spec.append(("ID", lambda data, skor: skor.get("_id", "")))
    spec.append(("Waktu Input", lambda data, skor: skor.get("_created_at", "")))

    # Karakteristik pasien
    for f in Q.PASIEN_FIELDS:
        spec.append((f["label"], d(f["name"])))
        if f["type"] == "radio_other":
            spec.append((f["other_label"], d(f["other_name"])))

    # PSQI isian 1-4
    for item in Q.PSQI_ISIAN:
        spec.append(("PSQI " + item["no"] + ". " + item["label"], d(item["name"])))

    # PSQI 5a-5j
    for name, huruf, teks in Q.PSQI_Q5_ITEMS:
        spec.append(("PSQI 5" + huruf + ". " + teks, d(name)))
    spec.append(("PSQI 5j keterangan", d(Q.PSQI_Q5J_OTHER)))

    # PSQI 6-10
    spec.append(("PSQI 6. " + Q.PSQI_Q6["label"], d(Q.PSQI_Q6["name"])))
    spec.append(("PSQI 7. " + Q.PSQI_Q7["label"], d(Q.PSQI_Q7["name"])))
    spec.append(("PSQI 8. " + Q.PSQI_Q8["label"], d(Q.PSQI_Q8["name"])))
    spec.append(("PSQI 9. " + Q.PSQI_Q9["label"], d(Q.PSQI_Q9["name"])))
    spec.append(("PSQI 10. " + Q.PSQI_Q10["label"], d(Q.PSQI_Q10["name"])))

    # PSQI 11a-e (laporan pasangan)
    for name, huruf, teks in Q.PSQI_Q11_ITEMS:
        spec.append(("PSQI 11" + huruf + ". " + teks, d(name)))
    spec.append(("PSQI 11e keterangan", d(Q.PSQI_Q11E_OTHER)))

    # PSQI skor
    def psqi_komp(kkey):
        return lambda data, skor, k=kkey: skor.get("psqi", {}).get("komponen", {}).get(k, "")
    for kkey, label in PSQI_KOMPONEN_LABEL.items():
        spec.append(("Skor " + label, psqi_komp(kkey)))
    spec.append(("PSQI Efisiensi (%)",
                 lambda data, skor: skor.get("psqi", {}).get("efisiensi_persen", "")))
    spec.append(("PSQI Skor Global",
                 lambda data, skor: skor.get("psqi", {}).get("skor_global", "")))
    spec.append(("PSQI Interpretasi",
                 lambda data, skor: skor.get("psqi", {}).get("interpretasi", "")))

    # DASS-21 item 1-21
    for nomor, kode, teks in Q.DASS_ITEMS:
        spec.append(("DASS " + str(nomor) + " (" + kode + ")", d("dass_q" + str(nomor))))

    # DASS-21 skor
    def dass_val(sub, field):
        return lambda data, skor, s=sub, f=field: skor.get("dass21", {}).get(s, {}).get(f, "")
    for sub, label in (("depresi", "Depresi"), ("cemas", "Cemas"), ("stres", "Stres")):
        spec.append(("DASS " + label + " (mentah)", dass_val(sub, "mentah")))
        spec.append(("DASS " + label + " (skor x2)", dass_val(sub, "skor")))
        spec.append(("DASS " + label + " (kategori)", dass_val(sub, "kategori")))

    return spec


SPEC = _build_spec()


def _record_to_dict(row):
    data = json.loads(row["data_json"])
    skor = json.loads(row["skor_json"])
    skor["_id"] = row["id"]
    skor["_created_at"] = row["created_at"]
    return data, skor


def export_csv(rows) -> bytes:
    """Terima daftar sqlite Row, kembalikan byte CSV (UTF-8 BOM)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([label for label, _ in SPEC])
    for row in rows:
        data, skor = _record_to_dict(row)
        writer.writerow([fn(data, skor) for _, fn in SPEC])
    return ("﻿" + buf.getvalue()).encode("utf-8")
