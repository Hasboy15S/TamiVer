# TamiVer — Web-Based Minecraft Server Manager

TamiVer adalah dashboard berbasis web yang ringan, aman, dan cantik untuk mengubah PC/Laptop kamu menjadi server Minecraft. Dikontrol sepenuhnya lewat browser!

![TamiVer Dashboard](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Modern-009688)

---

## ✨ Fitur Utama

- **Real-time Console**: Pantau jalannya server dan kirim command Minecraft langsung dari web (via WebSocket).
- **Minecraft Version Selector**: Ganti versi Minecraft (1.21.x, 1.20.x, dll) cukup dengan sekali klik dari dashboard. TamiVer akan otomatis mendownload file `.jar` resmi dari PaperMC.
- **Resource Monitoring**: Grafik *real-time* untuk memantau pemakaian CPU dan RAM (baik sistem host maupun proses Java).
- **Server Properties Editor**: Ubah settingan server seperti Port, MOTD, Max Players, dan Difficulty tanpa perlu repot buka text editor.
- **Multiplayer & TLauncher Ready**:
  - Ada *toggle* **Online Mode** agar pemain versi bajakan/TLauncher bisa masuk.
  - Info alamat LAN (IP Local) otomatis terdeteksi untuk mabar teman satu WiFi.
- **Aman**: Semua request dan akses WebSocket dilindungi oleh API Key.

---

## ⚙️ Cara Kerja Proyek Ini

TamiVer dibangun menggunakan arsitektur *asynchronous* modern dengan **FastAPI** di backend:

1. **Backend (Python & FastAPI)**: Bertugas sebagai "otak" penggerak. Backend ini menangani pengunduhan file Java (`server.jar`), lalu menjalankan proses server Minecraft di latar belakang (*background*) menggunakan modul `subprocess`.
2. **WebSockets**: Saat Minecraft berjalan, output teks dari terminal (stdout) dicegat oleh backend dan dipancarkan secara langsung (*streaming*) ke browser kamu menggunakan WebSocket. Begitu juga sebaliknya untuk pengiriman command. Pemantauan CPU/RAM dilakukan dengan library `psutil`.
3. **Frontend (HTML/JS/CSS)**: Antarmuka yang kamu lihat di browser dibangun murni dengan Vanilla JavaScript dan Tailwind CSS (tanpa framework berat seperti React/Vue), berkomunikasi dengan API backend secara *real-time*.

---

## 🚀 Cara Setup & Menjalankan

### 1. Persyaratan (Prerequisites)
Pastikan PC/Laptop kamu sudah terinstall dua hal ini:
- **Python** (Minimal versi 3.10) → Cek dengan mengetik `python --version` di terminal.
- **Java (JDK/JRE)** → Wajib diinstall dan dimasukkan ke Environment Variables (PATH).
  - Gunakan **Java 21** untuk Minecraft 1.20.5 ke atas.
  - Gunakan **Java 17** untuk Minecraft 1.18 sampai 1.20.4.

### 2. Instalasi
Buka Terminal atau PowerShell, lalu jalankan perintah berurutan ini:

```bash
# 1. Clone/Download repository ini
git clone https://github.com/Hasboy15S/TamiVer.git
cd TamiVer

# 2. Buat Virtual Environment (Sangat disarankan agar rapi)
python -m venv .venv

# 3. Aktifkan Virtual Environment
# Jika kamu pakai Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Jika kamu pakai Mac/Linux:
source .venv/bin/activate

# 4. Install semua library yang dibutuhkan
pip install -r requirements.txt
```

### 3. Konfigurasi (`.env`)
Server butuh konfigurasi dasar. Copy template `.env.example` menjadi `.env`.

```bash
# Di Windows:
copy .env.example .env
# Di Mac/Linux:
cp .env.example .env
```

Buka file `.env` yang baru dibuat dengan Notepad/Code Editor, dan **wajib ubah API_KEY**:
```dotenv
# Ganti dengan password rahasia kamu yang sulit ditebak
API_KEY=password_rahasia_tamiver_123

# RAM yang dialokasikan untuk Minecraft
MC_RAM_MIN=1G
MC_RAM_MAX=4G
```
*(Jangan pernah menyalakan server tanpa mengubah API_KEY bawaannya!)*

### 4. Jalankan TamiVer!
Pastikan Virtual Environment masih aktif, lalu ketik:
```bash
python main.py
```
Sekarang buka browser kesayanganmu dan kunjungi: **http://localhost:8000**

---

## 🎮 Panduan Pemakaian di Dashboard

1. Pertama kali buka web, ketik `API_KEY` rahasiamu di kotak pojok kanan atas, lalu klik **Save**.
2. Scroll ke bagian **Server Controls**, di kolom Minecraft Version, pilih versi yang ingin kamu mainkan lalu klik **Apply**. TamiVer akan men-download file servernya.
3. Di **Server Properties**, ubah sesuka hati (misal: matikan **Online Mode** jika pakai TLauncher), lalu klik **Save Properties**.
4. Klik tombol hijau **▶ Start Server**.
5. Pantau di **Live Console** sampai muncul tulisan `Done! For help, type "help"`.
6. Server siap dimainkan!

---

## 🌐 Mabar Jarak Jauh (Internet Play)

Jika kamu ingin mabar dengan teman yang beda kota/beda WiFi, kamu punya dua opsi:

**Opsi 1: Port Forwarding (Gratis, Perlu Akses Router)**
1. Login ke admin router/modem rumahmu (biasanya `192.168.1.1`).
2. Cari menu *Port Forwarding* atau *Virtual Server*.
3. Forward port `25565` (TCP/UDP) ke IP LAN laptopmu.
4. Berikan Public IP kamu ke temanmu.

**Opsi 2: Menggunakan playit.gg (Gratis, Anti Ribet, Tembus WiFi Sekolah)**
1. Daftar dan download agen [playit.gg](https://playit.gg).
2. Jalankan di laptopmu bersamaan dengan TamiVer.
3. Buat tunnel bertipe *Minecraft Java* (port 25565).
4. Kamu akan diberi alamat publik (misal: `kucing.auto.playit.gg`). Berikan alamat itu ke temanmu!
5. *(Bonus)* Jika kamu punya domain sendiri (misal dari Cloudflare), kamu bisa menggunakan **SRV Record** untuk menyambungkan domain aslimu ke playit.gg.
