import os
import json
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_kos_yevia_2026'

# Gunakan folder /tmp untuk Vercel (karena bersifat read-only di root)
# Jika di komputer lokal, akan otomatis membuat folder lokal
if os.environ.get('VERCEL'):
    DATA_FILE = '/tmp/data_kos.json'
    UPLOAD_FOLDER = '/tmp/uploads'
else:
    DATA_FILE = 'data_kos.json'
    UPLOAD_FOLDER = 'static/uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # Data awal default jika file belum ada di /tmp
    return {"kamar": [], "penghuni": [], "keuangan": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = 'Username atau Password salah!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    data = load_data()
    total_kamar = len(data['kamar'])
    terisi = sum(1 for k in data['kamar'] if k['status'] == 'Terisi')
    kosong = total_kamar - terisi
    return render_template('index.html', total=total_kamar, terisi=terisi, kosong=kosong)

@app.route('/kamar', methods=['GET', 'POST'])
@login_required
def kamar():
    data = load_data()
    if request.method == 'POST':
        nomor = request.form.get('nomor')
        harga = request.form.get('harga')
        fasilitas = request.form.get('fasilitas')
        
        new_kamar = {
            "id": len(data['kamar']) + 1,
            "nomor": nomor,
            "status": "Kosong",
            "penghuni": "-",
            "harga": harga,
            "fasilitas": fasilitas
        }
        data['kamar'].append(new_kamar)
        save_data(data)
        return redirect(url_for('kamar'))
        
    return render_template('kamar.html', daftar=data['kamar'])

@app.route('/kamar/hapus/<int:kamar_id>')
@login_required
def hapus_kamar(kamar_id):
    data = load_data()
    data['kamar'] = [k for k in data['kamar'] if k['id'] != kamar_id]
    save_data(data)
    return redirect(url_for('kamar'))

@app.route('/penghuni', methods=['GET', 'POST'])
@login_required
def penghuni():
    data = load_data()
    if request.method == 'POST':
        nama = request.form.get('nama')
        kamar_pilih = request.form.get('kamar')
        telepon = request.form.get('telepon')
        masuk = request.form.get('masuk')
        
        new_penghuni = {
            "id": len(data['penghuni']) + 1,
            "nama": nama,
            "kamar": kamar_pilih,
            "telepon": telepon,
            "masuk": masuk
        }
        data['penghuni'].append(new_penghuni)
        
        for k in data['kamar']:
            if k['nomor'] == kamar_pilih:
                k['status'] = 'Terisi'
                k['penghuni'] = nama
                
        save_data(data)
        return redirect(url_for('penghuni'))
        
    return render_template('penghuni.html', daftar=data['penghuni'], kamar_list=data['kamar'])

@app.route('/penghuni/hapus/<int:penghuni_id>')
@login_required
def hapus_penghuni(penghuni_id):
    data = load_data()
    target_penghuni = None
    
    for p in data['penghuni']:
        if p.get('id') == penghuni_id:
            target_penghuni = p
            break
            
    if target_penghuni:
        for k in data['kamar']:
            if k['nomor'] == target_penghuni['kamar']:
                k['status'] = 'Kosong'
                k['penghuni'] = '-'
                
    data['penghuni'] = [p for p in data['penghuni'] if p.get('id') != penghuni_id]
    save_data(data)
    return redirect(url_for('penghuni'))

@app.route('/keuangan', methods=['GET', 'POST'])
@login_required
def keuangan():
    data = load_data()
    if request.method == 'POST':
        tanggal = request.form.get('tanggal')
        keterangan = request.form.get('keterangan')
        jumlah = request.form.get('jumlah')
        file = request.files.get('bukti')
        
        filename = None
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        new_entry = {
            "id": len(data['keuangan']) + 1,
            "tanggal": tanggal,
            "keterangan": keterangan,
            "tipe": "Masuk",
            "jumlah": jumlah,
            "bukti": filename
        }
        
        data['keuangan'].insert(0, new_entry)
        save_data(data)
        return redirect(url_for('keuangan'))
        
    return render_template('keuangan.html', daftar=data['keuangan'])

@app.route('/keuangan/hapus/<int:keu_id>')
@login_required
def hapus_keuangan(keu_id):
    data = load_data()
    data['keuangan'] = [x for x in data['keuangan'] if x.get('id') != keu_id]
    save_data(data)
    return redirect(url_for('keuangan'))

if __name__ == '__main__':
    app.run(debug=True)