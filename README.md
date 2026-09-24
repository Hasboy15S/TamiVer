# TamiVer — Web-Based Minecraft Server Manager

TamiVer adalah dashboard berbasis web yang ringan, aman, dan cantik untuk mengubah PC/Laptop kamu menjadi server Minecraft. Dikontrol sepenuhnya lewat browser dengan UI ala aplikasi Pro!

![TamiVer Dashboard](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Modern-009688)

---

## ✨ Fitur Utama

- **Real-time Console**: Pantau jalannya server dan kirim command Minecraft (seperti `/op`, `/time set day`, dll) langsung dari web via WebSocket.
- **Dukungan Versi Terbaru & Fleksibel**: Bebas ganti versi Minecraft dengan sekali klik. TamiVer otomatis menarik *list* versi resmi (dari PaperMC) dan mendukung versi-versi paling baru sekalipun. Build atau versi *latest* terbaru langsung bisa di-*install* tanpa pusing.
- **Resource Monitoring**: Grafik *real-time* untuk memantau pemakaian CPU dan RAM (baik untuk keseluruhan laptop/PC maupun khusus proses Javanya).
- **Server Properties Editor**: Ubah settingan server seperti Port, MOTD, Max Players, Whitelist, dan Difficulty dengan tampilan visual (UI) yang rapi tanpa perlu repot mengedit file teks.
- **Multiplayer & TLauncher Ready**:
  - Terdapat fitur *toggle* **Online Mode** (matikan fitur ini agar pemain versi bajakan/TLauncher bisa masuk).
  - Info alamat LAN otomatis terdeteksi untuk memudahkan mabar teman satu WiFi.
- **Keamanan Penuh**: Setiap aksi, request API, dan WebSocket diamankan sepenuhnya menggunakan API Key pribadi kamu.

---

## 💻 Spesifikasi Minimum & Rekomendasi
Untuk menjalankan TamiVer beserta Server Minecraft di laptop/PC kamu dengan lancar, berikut adalah gambarannya:

- **OS**: Windows 10/11, macOS, atau Linux (Bebas!)
- **Prosesor (CPU)**: Minimal 2 Core (Sangat disarankan 4 Core ke atas)
- **RAM**: Minimal 4GB (Sangat disarankan 8GB ke atas, Minecraft *modern* lumayan rakus RAM)
- **Penyimpanan**: Minimal sisa ruang 2GB (Sangat disarankan pakai SSD agar *chunk loading* tidak *lag*)

> 💡 **Catatan**: Spek di atas sifatnya hanya **rekomendasi ideal**! Kalau kamu punya spek yang lebih "kentang" dan mau coba-coba, silakan di-pull repositori ini, *run* aja, dan bebas bereksperimen! Namanya juga ngoprek, hajar aja! 🔥

---

## 🚀 Panduan Detail Setup & Instalasi

### 1. Persiapan Awal (Prerequisites)
Pastikan dua alat ini sudah ter-install di komputermu:
- **Python** (Minimal versi 3.10). Cek dengan mengetik `python --version` di CMD/terminal.
- **Java (JDK/JRE)** (Wajib di-install dan didaftarkan di Environment Variables / Path komputermu).
  - **Java 21**: Wajib untuk Minecraft versi terbaru (1.20.5, 1.21.x ke atas).
  - **Java 17**: Untuk Minecraft versi lebih lama (1.18 sampai 1.20.4).
  *(Pastikan versi Java yang ter-install cocok dengan versi Minecraft yang kamu targetkan).*

### 2. Proses Instalasi
Buka Terminal / Command Prompt / PowerShell, lalu copy dan jalankan perintah ini secara berurutan:

```bash
# 1. Download kode sumber (Clone repository TamiVer)
git clone https://github.com/Hasboy15S/TamiVer.git
cd TamiVer

# 2. Buat Virtual Environment (Sangat disarankan agar modul Python laptopmu tidak berantakan)
python -m venv .venv

# 3. Aktifkan Virtual Environment
# Jika kamu menggunakan Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Jika kamu menggunakan Mac/Linux:
source .venv/bin/activate

# 4. Install semua kebutuhan sistem (Libraries)
pip install -r requirements.txt
```

### 3. Konfigurasi Sistem (`.env`)
TamiVer membutuhkan sedikit konfigurasi rahasia sebelum bisa menyala.
1. Copy file template konfigurasi menjadi `.env`:
   - Windows: `copy .env.example .env`
   - Mac/Linux: `cp .env.example .env`
2. Buka file `.env` yang baru dibuat dengan Notepad atau text editor.
3. **PENTING**: Wajib ubah isian `API_KEY`!
```dotenv
# Ganti dengan password rahasiamu (Ini akan ditanyakan saat pertama kali buka Web TamiVer)
API_KEY=bikin_password_mu_sendiri_yang_kuat

# Atur batasan alokasi RAM untuk Server Minecraft
MC_RAM_MIN=1G
MC_RAM_MAX=4G
```

### 4. Cara Menjalankan (Start) TamiVer
Setelah instalasi dan konfigurasi selesai, pastikan Virtual Environment-mu masih aktif (ada tulisan `(.venv)` di kiri terminal), lalu ketik:
```bash
python main.py
```
Kalau berhasil, terminal akan menampilkan *log* bahwa *dashboard* sudah jalan. **Jangan tutup terminal ini ya!**

Langkah selanjutnya:
1. Buka *browser* (Chrome/Edge/Brave).
2. Kunjungi alamat: `http://localhost:8000`
3. Masukkan `API_KEY` yang tadi kamu tulis di `.env` ke dalam kotak API Key di kiri atas web, lalu tekan **Save**.

---

## 🎮 Cara Menggunakan TamiVer (Dashboard)

1. **Install Engine**: Setelah *login* ke dashboard, lirik ke kotak **Engine & Version**. Pilih versi Minecraft yang mau kamu pakai. (Tersedia versi paling lawas hingga **rilis-rilis terbaru** yang langsung bisa dipilih). Lalu klik **Install**. Tunggu sebentar sampai statusnya "Ready".
2. **Atur Properties**: Turun ke kotak **Server Properties**. Silakan ubah Max Players, kesulitan, dan **wajib matikan fitur Online Mode** kalau kamu atau teman-temanmu mau main menggunakan akun gratisan/bajakan (*TLauncher* dkk). Setelah diubah, klik **Save Properties**.
3. **Mulai Server**: Klik tombol hijau raksasa **▶ Start Server**.
4. **Pantau Live Terminal**: Geser ke bagian bawah (Live Terminal). Tunggu proses *generate world* dan loading selesai. Kalau *console* terminal sudah memunculkan tulisan `Done! For help, type "help"`, berarti server sudah ON dan siap dimasuki!
5. **Mematikan Server**: Selalu dan wajib biasakan mematikan server menggunakan tombol **⏹ Stop Server** di dashboard TamiVer. Menutup terminal secara mendadak bisa menyebabkan kerusakan (corrupt) pada duniamu!

---

## 🌐 Panduan Mabar Jarak Jauh (Multiplayer)

Kalau kamu dan teman-temanmu kebetulan kumpul di satu tempat dan **terhubung ke WiFi yang sama**:
Cukup cek kotak **Connectivity > Local Network (LAN)** di web TamiVer. Kasih alamat/angka yang tertera di situ ke temanmu untuk dimasukkan ke menu *Multiplayer > Direct Connect* di Minecraft mereka.

Namun, kalau kalian **berada di beda kota / beda rumah**, gunakan metode ini:

**Opsi 1: Menggunakan playit.gg (Gratis, Tembus Segala WiFi, Anti Ribet!) — ⭐ Pilihan Terbaik**
1. Daftar akun dan *download* agent dari [playit.gg](https://playit.gg).
2. Jalankan aplikasi/program `playit` di laptopmu (dibiarkan menyala berbarengan dengan terminal TamiVer).
3. Buka dashboard web *playit*, tambahkan *tunnel* baru dengan tipe **Minecraft Java** (dan pastikan *port* mengarah ke `25565`).
4. Kamu akan diberi alamat publik (misal: `ayam-hitam.auto.playit.gg`).
5. Kasih alamat itu ke temanmu! Mereka tinggal masukin ke *Add Server* dan boom! Kalian bisa mabar!

**Opsi 2: Port Forwarding (Konvensional)**
1. Akses admin *router* modem rumahmu (biasanya lewat `192.168.1.1` di browser).
2. Cari pengaturan bernama *Port Forwarding* atau *Virtual Server*.
3. Buka port TCP & UDP untuk angka `25565` dan arahkan ke alamat IP lokal komputermu (IPv4 LAN).
4. Cari Public IP aslimu (lewat web _whatismyip_), dan berikan ke temanmu. *(Catatan: Kurang disarankan karena repot dan tidak semua provider internet (ISP) di Indonesia mendukung fitur ini karena adanya CGNAT).*
