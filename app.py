"""Aplikasi Flask: Form Karakteristik Pasien + PSQI + DASS-21.

Dirancang untuk di-hosting di PythonAnywhere (lihat README.md).
Created on 22/06/2026 by Timothy Subroto
"""
import secrets
from datetime import date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, abort, Response,
)

import db
import export
import questions as Q
from config import Config
from scoring import (
    hitung_semua, PSQI_KOMPONEN_LABEL, DASS_SUBSKALA_LABEL,
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
    return names


EXPECTED_FIELDS = _expected_fields()

# Field wajib (backstop di sisi server; HTML `required` adalah lini pertama).
REQUIRED_FIELDS = (
    [f["name"] for f in Q.PASIEN_FIELDS if f.get("required")]
    + [item["name"] for item in Q.PSQI_ISIAN]
    + ["psqi_q5a", "psqi_q5b", "psqi_q5c", "psqi_q5d", "psqi_q5e",
       "psqi_q5f", "psqi_q5g", "psqi_q5h", "psqi_q5i"]
    + ["psqi_q6", "psqi_q7", "psqi_q8", "psqi_q9"]
    + ["dass_q" + str(n) for n, _, _ in Q.DASS_ITEMS]
)


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


@app.route("/isi", methods=["GET", "POST"])
def isi():
    values = {}
    errors = []

    if request.method == "POST":
        if not _check_csrf():
            abort(400, "Token formulir tidak valid. Muat ulang halaman.")

        values = {name: request.form.get(name, "").strip()
                  for name in EXPECTED_FIELDS}

        # Validasi field wajib
        for name in REQUIRED_FIELDS:
            if not values.get(name):
                errors.append(name)

        if not errors:
            skor = hitung_semua(values)
            resp_id = db.simpan_response(values, skor)
            return redirect(url_for("hasil", resp_id=resp_id))

        flash("Masih ada pertanyaan wajib yang belum diisi. "
              "Bagian yang belum lengkap ditandai.", "error")
    else:
        values["tanggal"] = date.today().isoformat()

    return render_template(
        "form.html", Q=Q, values=values, errors=set(errors),
    )


@app.route("/hasil/<int:resp_id>")
def hasil(resp_id):
    row = db.ambil_satu(resp_id)
    if row is None:
        abort(404)
    import json
    data = json.loads(row["data_json"])
    skor = json.loads(row["skor_json"])
    return render_template(
        "hasil.html", data=data, skor=skor, resp_id=resp_id,
        psqi_label=PSQI_KOMPONEN_LABEL, dass_label=DASS_SUBSKALA_LABEL,
        dass_tabel=Q.DASS_TABEL_INTERPRETASI, public=True,
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
    rows = db.ambil_semua()
    return render_template("admin.html", rows=rows, total=len(rows))


@app.route("/admin/detail/<int:resp_id>")
@login_required
def admin_detail(resp_id):
    row = db.ambil_satu(resp_id)
    if row is None:
        abort(404)
    import json
    data = json.loads(row["data_json"])
    skor = json.loads(row["skor_json"])
    return render_template(
        "hasil.html", data=data, skor=skor, resp_id=resp_id,
        psqi_label=PSQI_KOMPONEN_LABEL, dass_label=DASS_SUBSKALA_LABEL,
        dass_tabel=Q.DASS_TABEL_INTERPRETASI, public=False,
        created_at=row["created_at"],
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
    today = date.today().isoformat()
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
