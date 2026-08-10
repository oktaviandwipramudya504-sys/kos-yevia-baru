from flask import Flask, render_template, request, redirect
import json
import os

app = Flask(__name__)

# Konfigurasi path file JSON: menggunakan /tmp jika di Vercel, lokal jika di laptop
if os.environ.get('VERCEL'):
    DATA_FILE = '/tmp/data_kos.json'
else:
    DATA_FILE = 'data_kos.json'

def load_data():
    # Pastikan folder /tmp tersedia jika berjalan di Vercel
    if os.environ.get('VERCEL'):
        tmp_dir = os.path.dirname(DATA_FILE)
        if tmp_dir and not os.path.exists(tmp_dir):
            try:
                os.makedirs(tmp_dir, exist_ok=True)
            except Exception:
                pass

    if not os.path.exists(DATA_FILE):
        initial_data = {
            "kamar": [],
            "penghuni": [],
            "transaksi": []
        }
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(initial_data, f, indent=4)
        except Exception:
            pass
        return initial_data
        
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"kamar": [], "penghuni": [], "transaksi": []}

def save_data(data):
    try:
        if os.environ.get('VERCEL'):
            tmp_dir = os.path.dirname(DATA_FILE)
            if tmp_dir and not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir, exist_ok=True)
                
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Error saving data:", e)

# --- DASHBOARD UTAMA ---
@app.route('/')
def index():
    data = load_data()
    total_kamar = len(data["kamar"])
    kamar_terisi = len([k for k in data["kamar"] if k.get('status') == 'Terisi'])
    kamar_kosong = total_kamar - kamar_terisi
    
    return render_template('index.html', 
                           total_kamar=total_kamar, 
                           kamar_terisi=kamar_terisi, 
                           kamar_kosong=kamar_kosong)

# --- ROUTE KELOLA KAMAR ---
@app.route('/kamar')
def kamar():
    data = load_data()
    return render_template('kamar.html', kamar_list=data["kamar"])

@app.route('/tambah_kamar', methods=['POST'])
def tambah_kamar():
    data = load_data()
    new_id = len(data["kamar"]) + 1
    
    new_room = {
        "id": new_id,
        "nomor_kamar": request.form['nomor_kamar'],
        "tipe": request.form['tipe'],
        "harga": int(request.form['harga']),
        "status": "Kosong"
    }
    
    data["kamar"].append(new_room)
    save_data(data)
    return redirect('/kamar')

@app.route('/hapus_kamar/<int:id>')
def hapus_kamar(id):
    data = load_data()
    data["kamar"] = [k for k in data["kamar"] if k["id"] != id]
    save_data(data)
    return redirect('/kamar')

# --- ROUTE PENGHUNI ---
@app.route('/penghuni')
def penghuni():
    data = load_data()
    kamar_kosong = [k for k in data["kamar"] if k.get('status') == 'Kosong']
    return render_template('penghuni.html', penghuni_list=data["penghuni"], kamar_kosong=kamar_kosong)

@app.route('/tambah_penghuni', methods=['POST'])
def tambah_penghuni():
    data = load_data()
    new_id = len(data["penghuni"]) + 1
    kamar_id = int(request.form['kamar_id'])
    
    nomor_kamar = ""
    for k in data["kamar"]:
        if k["id"] == kamar_id:
            k["status"] = "Terisi"
            nomor_kamar = k["nomor_kamar"]
            break
            
    new_tenant = {
        "id": new_id,
        "nama": request.form['nama'],
        "no_hp": request.form['no_hp'],
        "kamar_id": kamar_id,
        "nomor_kamar": nomor_kamar,
        "tanggal_masuk": request.form['tanggal_masuk'],
        "jatuh_tempo": request.form['jatuh_tempo']
    }
    
    data["penghuni"].append(new_tenant)
    save_data(data)
    return redirect('/penghuni')

@app.route('/hapus_penghuni/<int:id>')
def hapus_penghuni(id):
    data = load_data()
    for p in data["penghuni"]:
        if p["id"] == id:
            k_id = p["kamar_id"]
            for k in data["kamar"]:
                if k["id"] == k_id:
                    k["status"] = "Kosong"
            break
            
    data["penghuni"] = [p for p in data["penghuni"] if p["id"] != id]
    save_data(data)
    return redirect('/penghuni')

# --- ROUTE KEUANGAN ---
@app.route('/keuangan')
def keuangan():
    data = load_data()
    return render_template('keuangan.html', transaksi_list=data["transaksi"])

@app.route('/tambah_transaksi', methods=['POST'])
def tambah_transaksi():
    data = load_data()
    new_id = len(data["transaksi"]) + 1
    
    new_trx = {
        "id": new_id,
        "tanggal": request.form['tanggal'],
        "jenis": request.form['jenis'],
        "kategori": request.form['kategori'],
        "jumlah": int(request.form['jumlah']),
        "keterangan": request.form['keterangan']
    }
    
    data["transaksi"].append(new_trx)
    save_data(data)
    return redirect('/keuangan')

if __name__ == '__main__':
    app.run(debug=True)