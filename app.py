from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)

# PENTING: Ganti dengan string acak yang aman untuk enkripsi session
app.secret_key = 'kunci_rahasia_anda_yang_sangat_aman'

# Konfigurasi username dan password sederhana (bisa juga diambil dari Database/Environment Variable)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"  # Ubah nanti sesuai keinginan

# Dekorator untuk memproteksi halaman agar butuh login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rute Utama (Diproteksi)
@app.route('/')
@login_required
def index():
    # Logika halaman utama / dashboard kos Anda di sini
    return render_template('index.html')

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