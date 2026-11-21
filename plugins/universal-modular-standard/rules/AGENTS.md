# Universal Modular Architecture & LaTeX Standard

Aturan rekayasa universal ini berlaku untuk **semua proyek** (kode lintas bahasa, riset data/kuantitatif, sistem tertanam, hingga dokumen terkompilasi seperti LaTeX dan Markdown panjang).

## 1. Batas Ukuran Berkas & Anti-Monolitik (Hard Invariant)
- **Batas Maksimal Modul:** Setiap berkas sumber (kode maupun `.tex`) **wajib 120–150 baris (maksimal keras 150 LOC)**. Pecah menurut *Single Responsibility Principle* (*one reason to change*).
- **Thin Orchestrator:** Berkas utama (`main`, `index`, `app`, `makalah.tex`, `laporan.tex`, `ppt.tex`) **wajib < 80 baris** dan hanya menginisialisasi konfigurasi serta merakit pemanggilan modul.

## 2. Dekomposisi Ortogonal & Topologi Universal
Pisahkan tanggung jawab ke lima lapisan ortogonal:
1. **Thin Orchestrator:** Entrypoint tipis (`< 80` LOC).
2. **Externalized Config:** Parameter, konstanta, skema, dan *preamble* LaTeX di `config/` (atau `.sumber/config/`). Dilarang *hardcoding* di logika inti.
3. **Pure Core / Konten Inti:** Logika domain deterministik bebas I/O/UI di `src/core/` (atau modul konten `.sumber/bagian/` / `.sumber/slide/`).
4. **Boundary Adapters:** Interaksi I/O, UI, jaringan, API, DB, dan sistem berkas di `src/adapters/`.
5. **Shared Primitives:** Utilitas bersama dan kontrak tipe eksplisit (DRY).

**Topologi Kode Universal:** `config/`, `src/{core,modules,adapters}/`, `assets/`, `tests/`, `docs/`. Pada proyek multi-folder atau riset, terapkan topologi ini di dalam folder `code/`.

## 3. Arah Dependensi & Eksekusi Bertahap
- **Graf Asiklik (DAG):** Bebas *circular dependency*. `adapters/` boleh bergantung ke `core/`, tetapi **`core/` dilarang keras bergantung ke `adapters/`**.
- **Kontrak Eksplisit:** Wajib *type annotations* / skema validasi pada setiap batas modul.
- **Incremental Generation:** Rancang dan tampilkan peta direktori lebih dulu sebelum menulis implementasi; tulis/refaktor modul demi modul untuk mencegah pemotongan keluaran.

## 4. Standar Wajib LaTeX (Makalah, Laporan, PPT) & Fast-Scan
Setiap pembuatan atau modifikasi dokumen LaTeX wajib mengikuti skill `latex-modular-workflow`:
- **Nama Berkas Utama (`< 80` LOC di root dokumen):**
  - Makalah / Artikel: **`makalah.tex`** ($\to$ `makalah.pdf`)
  - Laporan / Proposal / Skripsi: **`laporan.tex`** ($\to$ `laporan.pdf`)
  - Presentasi Beamer: **`ppt.tex`** ($\to$ `ppt.pdf`)
- **Folder Dekomposisi `.sumber/`:** Berisi `config/` (`00_preamble.tex`, `00_macros.tex`), modul isi `NN_slug.tex` ($\le 150$ LOC/berkas), `gambar/`, `references.bib`, `INDEX.json`, dan `.build/` (isolasi `.aux`/`.log`/`.toc` via `--output-directory=.sumber/.build`).
- **Percepatan *Scanning* Agen:**
  1. Baca `.sumber/INDEX.json` atau jalankan `rg -n "^% @(module|sections|labels):" .sumber/` **sebelum** membuka berkas `.tex` lain.
  2. Awali tiap berkas `.tex` di `.sumber/` dengan header 4 baris (`% @module:`, `% @sections:`, `% @labels:`, `% @deps:`).
  3. Pakai prefiks `\label` baku (`sec:`, `def:`, `thm:`, `lem:`, `prop:`, `cor:`, `eq:`, `fig:`, `tab:`) dan *semantic line breaks* (1 kalimat/baris).
  4. Mutakhirkan `.sumber/INDEX.json` menggunakan `tex_index` (`skills/latex-modular-workflow/main.py`) setelah suntingan selesai.
