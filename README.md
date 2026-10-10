# Tugas 1 MMAI1001 — Visualisasi Jalur Terpendek

Aplikasi ini digunakan untuk membaca data graf berbobot, menghitung jalur terpendek (shortest path) menggunakan Algoritma **Dijkstra** dan **Bellman–Ford**, serta membandingkan total bobot minimum dan waktu eksekusinya secara real-time. Dilengkapi dengan dashboard interaktif berbasis Tkinter untuk memvisualisasikan alur pencarian algoritma langkah demi langkah.

## Prasyarat & Kebutuhan Sitem 

- Python 3.10 atau lebih baru.
- Tkinter (umumnya sudah terpasang bersama Python di Windows/macOS; pada sebagian Linux perlu paket `python3-tk`).
- Tidak memerlukan Python Standard Library (tanpa butuh `pip install` atau koneksi internet).

## Cara Menjalankan Aplikasi

Pastikan seluruh berkas proyek diletakkan dalam folder/direktori yang sama:

```text
python MMAIKelompok4.py
```

Jika perintah `python` tidak tersedia, coba `python3`. Di Windows dapat juga memakai `py`.

**Panduan Penggunaan GUI:**
1. Aplikasi akan otomatis membaca berkas `graf.txt` di folder yang sama.
2. Pilih simpul awal dan tujuan jika ingin mengubah pasangan dari baris terakhir berkas.
3. Klik **Hitung & bandingkan** untuk menghitung dan membandingkan hasil kedua algoritma.
4. Klik kartu **Dijkstra** atau **Bellman-Ford** untuk melihat langkah algoritma tersebut. Gunakan tombol **Putar**, tombol panah, atau penggeser waktu untuk menelusuri proses. Pilih kecepatan animasi di bawah graf.
5. Klik simpul pada graf untuk menjadikannya awal; **Shift+klik** untuk menjadikannya tujuan. Hasil akan dihitung ulang. Bilah atas selalu menampilkan rute, bobot, dan kesesuaian kedua algoritma.
6. Klik tombol **+Buka berkas graf** untuk memuat dataset graf lain (tersedia contoh berkas graf_contoh_C.txt). 


**Mode Baris Perintah (CLI/Tanpa GUI:)**
Untuk eksekusi cepat atau lingkungan headless (tanpa layar), gunakan opsi --cli:

```text
python MMAIKelompok4.py --cli
python MMAIKelompok4.py --cli --file graf_contoh_C.txt
```

**Uji otomatis:**
Untuk memverifikasi kebenaran logika algoritma dan pengujian kondisi ekstrem (edge cases):

```text
python uji_program.py
```

## Format berkas Input Graf
Berkas graf ditulis dalam format struktur data dictionary Python sederhana beserta baris penentu simpul awal dan tujuan:

```python
graph = {
    'A': {'B': 4, 'C': 2},
    'B': {'A': 4},
    'C': {}
}
A C
```

Aturan Format File Input:
- Nama variabel utama boleh menggunakan `graph` atau `graf`.
- Baris terakhir wajib berisi dua string dipisahkan spasi:
    VERTEKS_AWAL VERTEKS_AKHIR.
- Kunci (key) harus berupa nama simpul (string non-kosong) dan nilai (value) berupa dictionary berisi simpul tetangga beserta bobotnya.
- Bobot sisi wajib berupa angka numerik (integer/float) dan non-negatif.
- Untuk sisi dua arah (undirected edge), definisikan entri bolak-balik di kedua simpul.
- Keamanan Data: Pembacaan file memanfaatkan parser aman (ast.literal_eval), sehingga eksekusi kode berbahaya (code injection) di dalam berkas .txt akan diabaikan dan ditolak.

Masukan diproses sebagai data literal, sehingga kode dalam `graf.txt` tidak dijalankan.

## Catatan Implementasi dan Keluaran

- **Jalur** dan **bobot minimum** Jika tujuan terjangkau, aplikasi mengembalikan rantai lintasan beserta total bobot minimumnya. Jika tidak terjangkau, jalur bernilai kosong dan bobot ditampilkan sebagai `∞`.
- **Waktu algoritma** memakai `time.perf_counter()` dalam milidetik. Pengukuran ini hanya mencakup eksekusi kalkulasi algoritma dan pencatatan langkah animasi, tanpa memperhitungkan waktu gambar GUI atau pembacaan berkas.
- **Posisi simpul** pada kanvas dihitung secara otomatis menggunakan algoritma Breadth-First Search (BFS) berdasarkan tingkat kedalaman dari simpul awal, sehingga graf dapat dirender dengan rapi tanpa koordinat manual.


## Struktur File

| Berkas | Isi |
|---|---|
| `MMAIKelompok4.py` | Parser, algoritma, CLI, dan titik masuk GUI |
| `tampilan.py` | Dashboard Tkinter dan animasi interaktif |
| `graf.txt` | Contoh V1 sampai V15, awal V1 dan tujuan V15 |
| `graf_contoh_C.txt` | Contoh A sampai J, awal B dan tujuan H |
| `uji_program.py` | Uji tiga contoh soal dan beberapa kondisi batas |
