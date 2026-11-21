---
name: modular-architecture
description: >-
  Universal software engineering and file-organization protocol for all codebases
  (apps, backends, data/quantitative research, embedded systems). Use whenever
  designing, scaffolding, or refactoring any project to enforce 120-150 LOC limits,
  5-layer orthogonal decomposition, DAG dependencies, and incremental generation.
---

# Universal Modular Architecture Workflow

Skill ini memandu perancangan, implementasi, dan refaktor proyek lintas bahasa agar bebas dari berkas monolitik, mudah diuji, dan cepat dipindai oleh agen.

## 1. Hard Invariants (Tidak Bisa Ditawar)

1. **Batas Ukuran Berkas Sumber:** Maksimal **120–150 baris (LOC)** per berkas. Jika melewati 150 baris, pecah berdasarkan *Single Responsibility Principle* (*one reason to change*).
2. **Thin Orchestrator:** Entrypoint (`main.*`, `index.*`, `app.*`) **wajib < 80 baris**; hanya memuat konfigurasi, merakit dependensi (*composition root*), dan memanggil modul.
3. **Externalized Config:** Nol angka ajaib (*magic numbers*), path hardcoded, atau konstanta domain di dalam logika inti; simpan di `config/`.
4. **Pure Core Bebas Efek Samping:** `src/core/` berisi fungsi/algoritma deterministik murni. Dilarang melakukan I/O disk, panggilan HTTP, query DB, atau manipulasi UI di dalam `core/`.
5. **Graf Dependensi Asiklik (DAG):** `adapters/` $\to$ `modules/` $\to$ `core/`. Modul `core/` **dilarang keras** mengimpor `adapters/` atau framework eksternal.

## 2. Topologi Direktori Universal

### A. Proyek Perangkat Lunak / Layanan / Sistem Tertanam
```text
project_root/
├── main.* / app.*         # Thin Orchestrator (< 80 LOC)
├── config/                # Parameter, skema validasi, konstanta, env
├── src/
│   ├── core/              # Logika domain murni, kontrak tipe/interface
│   ├── modules/           # Fitur terpisah (vertical slice) atau sub-layanan
│   └── adapters/          # Antarmuka I/O, UI/view, HTTP/API, DB, filesystem
├── assets/                # Data mentah, berkas statis, media
├── tests/                 # Pengujian terisolasi (mencerminkan struktur src/)
└── docs/                  # Spesifikasi arsitektur & metodologi
```

### B. Proyek Riset Data / Kuliah (`University/` & Portofolio)
Ketika repositori memakai palet 8 folder (`data/`, `code/`, `naskah/`, `referensi/`, `deskripsi/`, `catatan/`, `materi/`, `arsip/`), terapkan topologi universal di dalam `code/` (`code/config/`, `code/src/{core,modules,adapters}/`, `code/tests/`) dan standar `.sumber/` di dalam `naskah/`.

## 3. Kontrak Eksplisit Antar-Modul

1. **Pengetikan Statis & Skema:** Gunakan `TypedDict`/`dataclass`/Pydantic (Python), `interface`/`type`/Zod (TS), `struct`/trait (Rust/Go), atau skema eksplisit pada setiap batas modul.
2. **Boundary Adapters:** Bungkus seluruh pustaka eksternal (`requests`, `sqlite3`, `pandas` I/O, React DOM, GPIO) di `src/adapters/` agar `core/` dapat diuji unit secara instan tanpa *mocking* rumit.
3. **Shared Primitives:** Ekstrak helper umum dan tipe dasar ke `src/core/contracts.*` atau `src/core/primitives.*` agar bebas duplikasi (*DRY*).

## 4. Protokol Eksekusi Bertahap (Wajib)

Ikuti urutan ini setiap kali membangun atau merefaktor sistem:
1. **Peta Struktur Terlebih Dahulu:** Rancang dan tampilkan pohon direktori beserta tanggung jawab & perkiraan LOC tiap berkas sebelum menulis kode.
2. **Tahap 1 — Config & Contracts:** Tulis `config/` dan `src/core/contracts.*` terlebih dahulu.
3. **Tahap 2 — Pure Core & Modules:** Implementasikan satu modul `core/` per langkah, langsung lengkapi unit test di `tests/`.
4. **Tahap 3 — Boundary Adapters:** Implementasikan adaptor I/O/UI/DB yang bergantung pada kontrak `core/`.
5. **Tahap 4 — Thin Orchestrator & Audit LOC:** Rakit `main.*` (`< 80` LOC), jalankan seluruh tes, dan pastikan tidak ada berkas sumber $> 150$ LOC.
