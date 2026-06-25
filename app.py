"""Aplikasi Flask: Form Karakteristik Pasien + PSQI + DASS-21.

Dirancang untuk di-hosting di PythonAnywhere (lihat README.md).
Created on 22/06/2026 by Timothy Subroto
"""
import secrets
from functools import wraps

import waktu

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, abort, Response, jsonify,
)

import db
import export
import questions as Q
from config import Config
from scoring import (
    hitung_semua, bandingkan, psqi_dinilai, dass_dinilai,
    PSQI_KOMPONEN_LABEL, DASS_SUBSKALA_LABEL, MOCA_DOMAIN_LABEL,
)

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi database saat aplikasi dimuat (aman dipanggil berulang).
db.init_db()


# ---------------------------------------------------------------------------
# Daftar field yang diharapkan & yang wajib diisi
# ---------------------------------------------------------------------------
def _expected_fields():
    names = []
    for f in Q.PASIEN_FIELDS:
        names.append(f["name"])
        if f["type"] == "radio_other":
            names.append(f["other_name"])
    for item in Q.PSQI_ISIAN:
        names.append(item["name"])
    for name, _, _ in Q.PSQI_Q5_ITEMS:
        names.append(name)
    names.append(Q.PSQI_Q5J_OTHER)
    names += [Q.PSQI_Q6["name"], Q.PSQI_Q7["name"], Q.PSQI_Q8["name"],
              Q.PSQI_Q9["name"], Q.PSQI_Q10["name"]]
    for name, _, _ in Q.PSQI_Q11_ITEMS:
        names.append(name)
    names.append(Q.PSQI_Q11E_OTHER)
    for nomor, _, _ in Q.DASS_ITEMS:
        names.append("dass_q" + str(nomor))
    for name, _, _, _ in Q.MOCA_DOMAINS:
        names.append(name)
    names.append(Q.MOCA_EDU_FIELD)
    return names


EXPECTED_FIELDS = _expected_fields()

# Field wajib (backstop di sisi server; HTML `required` adalah lini pertama).
# Hanya "Tanggal Pengambilan" & "Nama Responden" yang wajib; sisanya opsional.
REQUIRED_FIELDS = [f["name"] for f in Q.PASIEN_FIELDS if f.get("required")]


def _demographic_fields():
    """Nama field karakteristik pasien (untuk disalin ke pengukuran akhir)."""
    names = []
    for f in Q.PASIEN_FIELDS:
        names.append(f["name"])
        if f["type"] == "radio_other":
            names.append(f["other_name"])
    return names


DEMOGRAPHIC_FIELDS = _demographic_fields()
# Field demografi yang disalin ke pengukuran lanjutan (kecuali per-kunjungan).
COPYABLE_FIELDS = [f for f in DEMOGRAPHIC_FIELDS if f not in Q.FIELDS_TIDAK_DISALIN]

FASE_LABEL = {"awal": "Pengukuran Awal", "akhir": "Pengukuran Lanjutan"}


def _row_fase(row):
    try:
        return row["fase"] or "awal"
    except (KeyError, IndexError):
        return "awal"


def _lengkapi_dinilai(data, skor):
    """Pastikan flag `dinilai` PSQI & DASS ada pada skor tersimpan (record lama
    belum punya). Dihitung dari jawaban mentah agar akurat untuk data lama."""
    skor.setdefault("psqi", {}).setdefault("dinilai", psqi_dinilai(data))
    skor.setdefault("dass21", {}).setdefault("dinilai", dass_dinilai(data))
    return skor


# ---------------------------------------------------------------------------
# CSRF sederhana berbasis session
# ---------------------------------------------------------------------------
def get_csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


@app.context_processor
def inject_globals():
    return {
        "csrf_token": get_csrf_token,
        "app_title": app.config["APP_TITLE"],
        "app_subtitle": app.config["APP_SUBTITLE"],
    }


def _check_csrf():
    token = session.get("_csrf")
    return token and request.form.get("_csrf") == token


# ---------------------------------------------------------------------------
# Autentikasi admin
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Rute publik
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", total=db.hitung_total())


def _collect_and_validate():
    """Ambil seluruh field dari form POST + daftar field wajib yang kosong."""
    values = {name: request.form.get(name, "").strip()
              for name in EXPECTED_FIELDS}
    errors = [name for name in REQUIRED_FIELDS if not values.get(name)]
    return values, errors


def _resolve_parent(is_admin):
    """Validasi field tersembunyi `parent_id` untuk menautkan pengukuran
    lanjutan. Hanya admin yang boleh menautkan; parent harus pengukuran AWAL
    yang valid. Satu pasien boleh punya banyak pengukuran lanjutan.
    Kembalikan (fase, parent_id, raw_value)."""
    raw = (request.form.get("parent_id") or "").strip()
    if is_admin and raw.isdigit():
        awal = db.ambil_satu(int(raw))
        if awal is not None and _row_fase(awal) == "awal":
            return "akhir", int(raw), raw
    return "awal", None, raw


@app.route("/isi", methods=["GET", "POST"])
def isi():
    values = {}
    errors = []
    is_admin = bool(session.get("is_admin"))

    if request.method == "POST":
        if not _check_csrf():
            abort(400, "Token formulir tidak valid. Muat ulang halaman.")

        values, errors = _collect_and_validate()
        fase, parent_id, raw_parent = _resolve_parent(is_admin)
        if not errors:
            skor = hitung_semua(values)
            resp_id = db.simpan_response(values, skor, fase=fase,
                                         parent_id=parent_id)
            if fase == "akhir":
                flash("Pengukuran lanjutan tersimpan.", "ok")
                return redirect(url_for("admin_banding", pasien_id=parent_id))
            return redirect(url_for("hasil", resp_id=resp_id))

        # Pertahankan tautan pengukuran akhir saat render ulang.
        values["parent_id"] = raw_parent
        flash("Masih ada pertanyaan wajib yang belum diisi. "
              "Bagian yang belum lengkap ditandai.", "error")
    else:
        values["tanggal"] = waktu.hari_ini().isoformat()

    return render_template(
        "form.html", Q=Q, values=values, errors=set(errors),
        form_action=url_for("isi"), fase="awal", can_search=is_admin,
    )


@app.route("/admin/cari-pasien")
@login_required
def admin_cari_pasien():
    """Autolengkap: cari pasien (pengukuran awal) untuk pengukuran lanjutan."""
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return jsonify([])
    rows = db.cari_pasien(q)
    return jsonify([
        {"id": r["id"], "nama": r["nama"], "no_rm": r["no_rm"],
         "tanggal": r["tanggal"], "usia": r["usia"]}
        for r in rows
    ])


@app.route("/admin/pasien/<int:pasien_id>/data")
@login_required
def admin_pasien_data(pasien_id):
    """Kembalikan data demografi satu pasien (untuk mengisi otomatis form akhir)."""
    row = db.ambil_satu(pasien_id)
    if row is None or _row_fase(row) != "awal":
        abort(404)
    import json
    data = json.loads(row["data_json"])
    demografi = {k: data.get(k, "") for k in COPYABLE_FIELDS}
    return jsonify({"nama": row["nama"], "demografi": demografi})


@app.route("/hasil/<int:resp_id>")
def hasil(resp_id):
    row = db.ambil_satu(resp_id)
    if row is None:
        abort(404)
    import json
    data = json.loads(row["data_json"])
    skor = _lengkapi_dinilai(data, json.loads(row["skor_json"]))
    fase = _row_fase(row)
    return render_template(
        "hasil.html", data=data, skor=skor, resp_id=resp_id,
        psqi_label=PSQI_KOMPONEN_LABEL, dass_label=DASS_SUBSKALA_LABEL,
        moca_label=MOCA_DOMAIN_LABEL,
        dass_tabel=Q.DASS_TABEL_INTERPRETASI, public=True,
        fase=fase, fase_label=FASE_LABEL.get(fase, ""),
    )


# ---------------------------------------------------------------------------
# Rute admin
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not _check_csrf():
            abort(400)
        password = request.form.get("password", "")
        if secrets.compare_digest(password, app.config["ADMIN_PASSWORD"]):
            session["is_admin"] = True
            nxt = request.args.get("next") or url_for("admin")
            return redirect(nxt)
        flash("Password salah.", "error")
    return render_template("login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Anda telah keluar.", "ok")
    return redirect(url_for("index"))


@app.route("/admin")
@login_required
def admin():
    import json
    pasien = []
    for r in db.ambil_pasien_list():
        d = dict(r)
        try:
            ans = json.loads(r["data_json"])
        except (ValueError, TypeError):
            ans = {}
        d["cogstim"] = ans.get("cogstim_explained") in ("1", "on", "true", "Ya")
        d["psqi_dinilai"] = psqi_dinilai(ans)
        d["dass_dinilai"] = dass_dinilai(ans)
        pasien.append(d)
    return render_template("admin.html", pasien=pasien, total=len(pasien))


@app.route("/admin/detail/<int:resp_id>")
@login_required
def admin_detail(resp_id):
    row = db.ambil_satu(resp_id)
    if row is None:
        abort(404)
    import json
    data = json.loads(row["data_json"])
    skor = _lengkapi_dinilai(data, json.loads(row["skor_json"]))
    fase = _row_fase(row)

    # Konteks longitudinal: id pasien (pengukuran awal) & jumlah pengukuran.
    pid = resp_id if fase == "awal" else row["parent_id"]
    n_pengukuran = db.jumlah_pengukuran(pid) if pid else 1
    banding_ada = n_pengukuran > 1
    bisa_tambah_akhir = pid is not None  # boleh menambah pengukuran kapan saja

    return render_template(
        "hasil.html", data=data, skor=skor, resp_id=resp_id,
        psqi_label=PSQI_KOMPONEN_LABEL, dass_label=DASS_SUBSKALA_LABEL,
        moca_label=MOCA_DOMAIN_LABEL,
        dass_tabel=Q.DASS_TABEL_INTERPRETASI, public=False,
        created_at=row["created_at"],
        fase=fase, fase_label=FASE_LABEL.get(fase, ""),
        kontrol=row["kontrol_berikutnya"],
        pasien_id=pid, banding_ada=banding_ada,
        bisa_tambah_akhir=bisa_tambah_akhir,
    )


@app.route("/admin/edit/<int:resp_id>", methods=["GET", "POST"])
@login_required
def admin_edit(resp_id):
    row = db.ambil_satu(resp_id)
    if row is None:
        abort(404)
    import json
    errors = []

    if request.method == "POST":
        if not _check_csrf():
            abort(400)
        values, errors = _collect_and_validate()
        if not errors:
            skor = hitung_semua(values)
            db.update_response(resp_id, values, skor)
            flash("Data responden #%d berhasil diperbarui." % resp_id, "ok")
            return redirect(url_for("admin_detail", resp_id=resp_id))
        flash("Masih ada pertanyaan wajib yang belum diisi. "
              "Bagian yang belum lengkap ditandai.", "error")
    else:
        values = json.loads(row["data_json"])

    fase = _row_fase(row)
    return render_template(
        "form.html", Q=Q, values=values, errors=set(errors),
        form_action=url_for("admin_edit", resp_id=resp_id),
        edit_id=resp_id, edit_nama=row["nama"],
        fase=fase, fase_label=FASE_LABEL.get(fase, ""),
    )


@app.route("/admin/pasien/<int:pasien_id>/akhir", methods=["GET", "POST"])
@login_required
def admin_akhir(pasien_id):
    """Tambah pengukuran LANJUTAN untuk pasien tertentu (boleh berkali-kali)."""
    awal = db.ambil_satu(pasien_id)
    if awal is None or _row_fase(awal) != "awal":
        abort(404)

    import json
    errors = []
    if request.method == "POST":
        if not _check_csrf():
            abort(400)
        values, errors = _collect_and_validate()
        if not errors:
            skor = hitung_semua(values)
            db.simpan_response(values, skor, fase="akhir", parent_id=pasien_id)
            flash("Pengukuran lanjutan berhasil disimpan.", "ok")
            return redirect(url_for("admin_banding", pasien_id=pasien_id))
        flash("Masih ada pertanyaan wajib yang belum diisi. "
              "Bagian yang belum lengkap ditandai.", "error")
    else:
        # Salin demografi (tanpa tanggal & jadwal kontrol) dari awal.
        awal_data = json.loads(awal["data_json"])
        values = {k: awal_data.get(k, "") for k in COPYABLE_FIELDS}
        values["tanggal"] = waktu.hari_ini().isoformat()

    ke = db.jumlah_pengukuran(pasien_id) + 1
    return render_template(
        "form.html", Q=Q, values=values, errors=set(errors),
        form_action=url_for("admin_akhir", pasien_id=pasien_id),
        fase="akhir", fase_label=FASE_LABEL["akhir"],
        akhir_nama=awal["nama"], akhir_pasien_id=pasien_id, akhir_ke=ke,
    )


@app.route("/admin/banding/<int:pasien_id>")
@login_required
def admin_banding(pasien_id):
    """Halaman tren: semua pengukuran satu pasien + selisih awal vs terakhir."""
    awal = db.ambil_satu(pasien_id)
    if awal is None or _row_fase(awal) != "awal":
        abort(404)
    rows = db.ambil_pengukuran_pasien(pasien_id)
    if len(rows) < 2:
        flash("Pasien ini belum memiliki pengukuran lanjutan.", "error")
        return redirect(url_for("admin_detail", resp_id=pasien_id))

    import json
    data = json.loads(awal["data_json"])
    pengukuran = []
    for i, r in enumerate(rows, 1):
        rdata = json.loads(r["data_json"])
        pengukuran.append({
            "no": i, "id": r["id"], "tanggal": r["tanggal"],
            "fase": _row_fase(r),
            "skor": _lengkapi_dinilai(rdata, json.loads(r["skor_json"])),
        })
    # Selisih pengukuran pertama vs terakhir.
    perbandingan = bandingkan(pengukuran[0]["skor"], pengukuran[-1]["skor"])
    return render_template(
        "banding.html", data=data, pengukuran=pengukuran,
        perbandingan=perbandingan, pasien_id=pasien_id,
        psqi_label=PSQI_KOMPONEN_LABEL, dass_label=DASS_SUBSKALA_LABEL,
        moca_label=MOCA_DOMAIN_LABEL,
    )


@app.route("/admin/hapus/<int:resp_id>", methods=["POST"])
@login_required
def admin_hapus(resp_id):
    if not _check_csrf():
        abort(400)
    db.hapus_satu(resp_id)
    flash("Data responden #%d telah dihapus." % resp_id, "ok")
    return redirect(url_for("admin"))


@app.route("/admin/export.csv")
@login_required
def admin_export():
    rows = db.ambil_semua(order_desc=False)
    csv_bytes = export.export_csv(rows)
    today = waktu.hari_ini().isoformat()
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename=data_psqi_dass21_{today}.csv"
        },
    )


# ---------------------------------------------------------------------------
# Error handler
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", kode=404,
                           pesan="Halaman tidak ditemukan."), 404


@app.errorhandler(400)
def bad_request(e):
    pesan = getattr(e, "description", "Permintaan tidak valid.")
    return render_template("error.html", kode=400, pesan=pesan), 400


if __name__ == "__main__":
    app.run(debug=True)
