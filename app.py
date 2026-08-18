import base64
import os
from functools import wraps
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.secret_key = "kunci_rahasia_kos_yevia_2026"

# Konfigurasi Database SQLite aman untuk Vercel (menggunakan /tmp jika di Vercel)
if os.environ.get("VERCEL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/kos.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kos.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# --- KONFIGURASI GITHUB API ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO_OWNER = "oktaviandwipramudya504-sys"
REPO_NAME = "kos-yevia-baru"
BRANCH = "main"


# --- MODEL DATABASE ---
class Kamar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nomor = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="Kosong")
    penghuni = db.Column(db.String(100), default="-")
    harga = db.Column(db.String(50), nullable=False)
    fasilitas = db.Column(db.Text, nullable=True)


class Penghuni(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    kamar = db.Column(db.String(50), nullable=False)
    telepon = db.Column(db.String(20), nullable=False)
    masuk = db.Column(db.String(50), nullable=False)


class Keuangan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.String(50), nullable=False)
    keterangan = db.Column(db.String(200), nullable=False)
    tipe = db.Column(db.String(20), nullable=False)  # Masuk / Keluar
    jumlah = db.Column(db.Integer, nullable=False)
    bukti = db.Column(db.String(300), nullable=True)  # Menyimpan URL publik GitHub


# Buat database otomatis saat pertama kali dijalankan
with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME
            and request.form.get("password") == ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Username atau Password salah!"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    daftar_kamar = Kamar.query.all()
    daftar_keuangan = Keuangan.query.all()

    total_kamar = len(daftar_kamar)
    terisi = sum(1 for k in daftar_kamar if k.status == "Terisi")
    kosong = total_kamar - terisi

    total_masuk = sum(x.jumlah for x in daftar_keuangan if x.tipe == "Masuk")
    total_keluar = sum(x.jumlah for x in daftar_keuangan if x.tipe == "Keluar")
    saldo_akhir = total_masuk - total_keluar

    return render_template(
        "index.html",
        total=total_kamar,
        terisi=terisi,
        kosong=kosong,
        saldo=saldo_akhir,
    )


@app.route("/kamar", methods=["GET", "POST"])
@login_required
def kamar():
    if request.method == "POST":
        new_kamar = Kamar(
            nomor=request.form.get("nomor"),
            status="Kosong",
            penghuni="-",
            harga=request.form.get("harga"),
            fasilitas=request.form.get("fasilitas"),
        )
        db.session.add(new_kamar)
        db.session.commit()
        return redirect(url_for("kamar"))

    daftar_kamar = Kamar.query.all()
    return render_template("kamar.html", daftar=daftar_kamar)


@app.route("/kamar/hapus/<int:kamar_id>")
@login_required
def hapus_kamar(kamar_id):
    target = Kamar.query.get_or_404(kamar_id)
    db.session.delete(target)
    db.session.commit()
    return redirect(url_for("kamar"))


@app.route("/penghuni", methods=["GET", "POST"])
@login_required
def penghuni():
    if request.method == "POST":
        nama = request.form.get("nama")
        kamar_pilih = request.form.get("kamar")

        new_penghuni = Penghuni(
            nama=nama,
            kamar=kamar_pilih,
            telepon=request.form.get("telepon"),
            masuk=request.form.get("masuk"),
        )
        db.session.add(new_penghuni)

        # Update status kamar jadi Terisi
        target_kamar = Kamar.query.filter_by(nomor=kamar_pilih).first()
        if target_kamar:
            target_kamar.status = "Terisi"
            target_kamar.penghuni = nama

        db.session.commit()
        return redirect(url_for("penghuni"))

    daftar_penghuni = Penghuni.query.all()
    kamar_list = Kamar.query.all()
    return render_template(
        "penghuni.html", daftar=daftar_penghuni, kamar_list=kamar_list
    )


@app.route("/penghuni/hapus/<int:penghuni_id>")
@login_required
def hapus_penghuni(penghuni_id):
    target_penghuni = Penghuni.query.get_or_404(penghuni_id)

    # Kembalikan status kamar jadi Kosong
    target_kamar = Kamar.query.filter_by(nomor=target_penghuni.kamar).first()
    if target_kamar:
        target_kamar.status = "Kosong"
        target_kamar.penghuni = "-"

    db.session.delete(target_penghuni)
    db.session.commit()
    return redirect(url_for("penghuni"))


@app.route("/keuangan", methods=["GET", "POST"])
@login_required
def keuangan():
    if request.method == "POST":
        tanggal = request.form.get("tanggal")
        keterangan = request.form.get("keterangan")
        tipe = request.form.get("tipe")
        jumlah = int(request.form.get("jumlah", 0))
        file = request.files.get("bukti")

        image_url = None
        if file and file.filename != "":
            filename = file.filename
            file_content = file.read()
            encoded_content = base64.b64encode(file_content).decode("utf-8")

            # Path penyimpanan di dalam repository GitHub
            path_in_repo = f"static/uploads/{filename}"
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path_in_repo}"

            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "vnd.github+json",
            }

            payload = {
                "message": f"Upload otomatis bukti pembayaran {filename}",
                "content": encoded_content,
                "branch": BRANCH,
            }

            # Kirim ke GitHub API
            response = requests.put(url, json=payload, headers=headers)

            if response.status_code in [200, 201]:
                # Dapatkan URL publik gambar dari raw.githubusercontent.com
                image_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{path_in_repo}"

        new_entry = Keuangan(
            tanggal=tanggal,
            keterangan=keterangan,
            tipe=tipe,
            jumlah=jumlah,
            bukti=image_url,
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for("keuangan"))

    daftar_keuangan = Keuangan.query.order_by(Keuangan.id.desc()).all()
    total_masuk = sum(x.jumlah for x in daftar_keuangan if x.tipe == "Masuk")
    total_keluar = sum(x.jumlah for x in daftar_keuangan if x.tipe == "Keluar")
    saldo_akhir = total_masuk - total_keluar

    return render_template(
        "keuangan.html",
        daftar=daftar_keuangan,
        masuk=total_masuk,
        keluar=total_keluar,
        saldo=saldo_akhir,
    )


@app.route("/keuangan/hapus/<int:keu_id>")
@login_required
def hapus_keuangan(keu_id):
    target = Keuangan.query.get_or_404(keu_id)
    db.session.delete(target)
    db.session.commit()
    return redirect(url_for("keuangan"))


if __name__ == "__main__":
    app.run(debug=True)