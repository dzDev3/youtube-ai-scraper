# 🎥 YouTube AI Comments Scraper + Google Sheets Integration

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API-green?style=for-the-badge&logo=google-sheets)
![YouTube API](https://img.shields.io/badge/YouTube%20API-v3-red?style=for-the-badge&logo=youtube)

Program otomasi berbasis Python untuk mengumpulkan dataset komentar dari YouTube secara cerdas. Dilengkapi dengan filter kualitas, dukungan pencarian berbasis kata kunci, dan integrasi otomatis langsung ke **Google Sheets**.

---

## ✨ Fitur Unggulan

- 🚀 **Otomasi Penuh**: Cari video, ambil statistik (View, Like, Durasi), dan tarik komentar dalam satu perintah.
- 📊 **Integrasi Google Sheets**: Hasil scraping langsung terkirim ke Google Sheets dengan format yang rapi.
- 🧹 **Pembersihan Data Otomatis**: Menghapus duplikat dan karakter sampah (line breaks) agar data siap diolah.
- 🎨 **Modern Terminal UI**: Tampilan output terminal yang berwarna (Colorama) dan informatif.
- 🔑 **Keamanan API**: Mendukung penggunaan file `.env` dan `service_account.json` untuk menjaga kerahasiaan kunci akses.
- 🛠️ **Customizable**: Tentukan sendiri jumlah video, target komentar, dan kata kunci melalui file eksternal.

---

## 📋 Struktur Kolom Dataset

Hasil akhir akan disimpan dalam satu tabel (Sheet) dengan urutan kolom sebagai berikut:
`NIM` | `Video_ID` | `Judul_Video` | `Channel` | `Durasi` | `Jumlah View` | `Jumlah Like` | `Jumlah Komentar` | `Topik` | `Tanggal_Video` | `URL_Video` | `Nama_Komentator` | `Teks_Komentar` | `Tanggal_Komentar`

---

## 🛠️ Prasyarat & Instalasi

### 1. Kloning Repository
```bash
git clone https://github.com/dzDev3/youtube-ai-scraper.git
cd youtube-ai-scraper
```

### 2. Instal Library yang Dibutuhkan
```bash
pip install requests pandas python-dotenv gspread google-auth colorama
```

### 3. Persiapan Kredensial
*   Dapatkan **YouTube Data API Key** dari [Google Cloud Console](https://console.cloud.google.com/).
*   Buat **Service Account**, unduh file JSON-nya, dan simpan sebagai `service_account.json` di folder utama.
*   Aktifkan **Google Sheets API** dan **Google Drive API** di Project Google Cloud Anda.
*   **Bagikan (Share)** Spreadsheet Anda ke email Service Account (sebagai Editor).

---

## 🚀 Cara Penggunaan

1.  Isi daftar kata kunci di file `keywords.txt`.
2.  Isi NIM Anda di file `nim.txt`.
3.  Siapkan file `.env` dengan isi: `YOUTUBE_API_KEY=KUNCI_API_ANDA`.
4.  Jalankan program:
    ```bash
    python main.py
    ```
5.  Masukkan URL Google Sheets saat diminta (pada jalankan pertama).
6.  Masukkan target jumlah video dan komentar.
7.  Pantau prosesnya di terminal dan lihat hasilnya di Google Sheets Anda secara real-time!

---

## 📂 Struktur File
*   `main.py`: Skrip utama program.
*   `keywords.txt`: Daftar kata kunci pencarian video.
*   `nim.txt`: Nomor Induk Mahasiswa pengumpul data.
*   `spreadsheet_url.txt`: Link target Google Sheets.
*   `.env.example`: Template pengaturan API Key.
*   `.gitignore`: Menjaga agar file sensitif tidak terupload ke publik.

---

## 🛡️ Disclaimer
Program ini dibuat untuk tujuan edukasi dan riset data. Pastikan untuk selalu mematuhi *Terms of Service* dari YouTube Data API dalam mengumpulkan data.

---
**Developed with ❤️ by [Dzdev3](https://github.com/dzDev3)**
