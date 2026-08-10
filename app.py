from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)

# PENTING: Ganti dengan string acak yang aman untuk enkripsi session
app.secret_key = 'kunci_rahasia_anda_yang_sangat_aman'

# Konfigurasi username dan password sederhana
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"

# Dekorator untuk memproteksi halaman agar butuh login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rute Utama / Dashboard (Diproteksi)
@app.route('/')
@login_required
def index():
    # Contoh data sementara untuk statistik dashboard (nanti bisa diambil dari database MySQL)
    total_kamar = 10
    kamar_terisi = 7
    kamar_kosong = 3
    
    return render_template('index.html', 
                           total_kamar=total_kamar, 
                           kamar_terisi=kamar_terisi, 
                           kamar_kosong=kamar_kosong)

# Rute Kelola Kamar
@app.route('/kamar')
@login_required
def kamar():
    return render_template('kamar.html')

# Rute Data Penghuni
@app.route('/penghuni')
@login_required
def penghuni():
    return "<h1>Halaman Data Penghuni (Segera Dibangun)</h1><a href='/'>Kembali ke Dashboard</a>"

# Rute Keuangan
@app.route('/keuangan')
@login_required
def keuangan():
    return "<h1>Halaman Arus Keuangan (Segera Dibangun)</h1><a href='/'>Kembali ke Dashboard</a>"

# Rute Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Username atau Password salah!'
            
    return render_template('login.html', error=error)

# Rute Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)