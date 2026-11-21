---
name: latex-modular-workflow
description: >-
  Standardized LaTeX decomposition workflow for makalah, laporan, and Beamer
  presentations (ppt). Enforces thin root entrypoints (makalah.tex, laporan.tex,
  ppt.tex), modular files inside .sumber/ (<= 150 LOC), fast-scan headers,
  .sumber/INDEX.json generation, and isolated .sumber/.build/ compilation.
---

# LaTeX Modular Workflow & Fast-Scan Protocol

Skill ini menstandarkan penyusunan dan pemindaian dokumen LaTeX agar agen AI dapat membaca, menganalisis, dan menyunting makalah, laporan, maupun slide presentasi Beamer secara super cepat tanpa membaca berkas monolitik.

## 1. Struktur Direktori Wajib

Berkas utama tipis (`< 80` LOC) berada di root folder dokumen, sementara seluruh dekomposisi `.tex`, aset, bibliografi, indeks, dan artefak build berada di `.sumber/`:

```text
<folder-dokumen>/               # mis. makalah/, laporan/, presentasi/, atau naskah/
├── makalah.tex                 # ATAU laporan.tex ATAU ppt.tex (< 80 LOC)
├── makalah.pdf                 # ATAU laporan.pdf ATAU ppt.pdf
└── .sumber/
    ├── INDEX.json              # Peta 1-baca otomatis (dihasilkan tex_index)
    ├── config/
    │   ├── 00_preamble.tex     # Paket, margin, font, style bab/tema (<= 150 LOC)
    │   └── 00_macros.tex       # Notasi matematika & lingkungan teorema (<= 150 LOC)
    ├── bagian/                 # Untuk makalah/laporan (atau slide/ untuk ppt.tex)
    │   ├── 01_pendahuluan.tex  # <= 150 LOC per berkas
    │   ├── 02_landasan_teori.tex
    │   └── ...
    ├── lampiran/               # Opsional: 90_lampiran_a.tex, dst. (<= 150 LOC)
    ├── gambar/                 # Seluruh grafik, diagram, logo
    ├── references.bib          # Bibliografi BibTeX
    └── .build/                 # Isolasi .aux, .log, .toc, .out, .bbl, .nav, .snm
```

### Penamaan Berkas Utama Berdasarkan Jenis Dokumen
| Jenis Dokumen | Berkas Entrypoint | Luaran PDF | Folder Modul Konten | Batas Modul |
| :--- | :--- | :--- | :--- | :--- |
| Makalah / Artikel Ilmiah | `makalah.tex` | `makalah.pdf` | `.sumber/bagian/` | $\le 150$ LOC |
| Laporan / Proposal / Skripsi | `laporan.tex` | `laporan.pdf` | `.sumber/bagian/` | $\le 150$ LOC |
| Presentasi LaTeX Beamer | `ppt.tex` | `ppt.pdf` | `.sumber/slide/` | $\le 150$ LOC (3–5 slide/berkas) |

## 2. Protokol Percepatan *Scanning* Agen (Fast-Scan)

Saat membuka proyek LaTeX yang sudah ada, ikuti urutan ini:
1. **Baca 1 Berkas Peta:** Baca `.sumber/INDEX.json` terlebih dahulu. Jika belum ada, jalankan `tex_index`:
   ```powershell
   python "~/.gemini\config\plugins\universal-modular-standard\skills\latex-modular-workflow\main.py" "<folder-dokumen>" --check
   ```
2. **Pindai Header Semantik (Fallback Instan):** Jalankan satu pencarian `rg`:
   ```bash
   rg -n "^% @(module|sections|labels|deps):" .sumber/
   ```
3. **Targetkan Baris Spesifik:** Gunakan `StartLine`/`EndLine` hanya pada modul relevan.

### Template Header Semantik 4 Baris (Wajib di Baris 1–4 Tiap `.tex` di `.sumber/`)
```tex
% @module: 02_landasan_teori
% @sections: 2.1 Definisi Ruang Metrik | 2.2 Sifat Kekonvergenan
% @labels: sec:landasan_teori, def:ruang_metrik, thm:lengkap, eq:cauchy
% @deps: config/00_preamble.tex, config/00_macros.tex
```

### Konvensi Penulisan `.tex` Ramah *Scanning*
- **Prefiks `\label` Wajib:** `sec:`, `def:`, `thm:`, `lem:`, `prop:`, `cor:`, `eq:`, `fig:`, `tab:`, `alg:`.
- ***Semantic Line Breaks*:** Tulis **1 kalimat per baris** pada paragraf narasi agar `rg` menampilkan kalimat utuh dan `edit_file` presisi per baris.
- **Pecah Bab Panjang:** Jika satu bab/topik melebihi 150 baris, pecah menjadi sub-modul bernomor (`04a_hasil_deskriptif.tex`, `04b_hasil_inferensial.tex`).

## 3. Template Entrypoint Tipis (`< 80` LOC)

```tex
% Entrypoint orkestrator tipis (< 80 baris)
\input{.sumber/config/00_preamble.tex}
\input{.sumber/config/00_macros.tex}

\begin{document}
\input{.sumber/bagian/00_sampul_abstrak.tex}
\input{.sumber/bagian/01_pendahuluan.tex}
\input{.sumber/bagian/02_metode.tex}
\input{.sumber/bagian/03_hasil_pembahasan.tex}
\input{.sumber/bagian/04_simpulan.tex}
\input{.sumber/bagian/05_daftar_rujukan.tex}
\end{document}
```
*(Untuk `00_preamble.tex`, sertakan `\graphicspath{{.sumber/gambar/}{gambar/}}` agar `\includegraphics{nama_file.png}` selalu pendek dan portabel.)*

## 4. Kompilasi Bersih & Verifikasi

Selalu kompilasi menggunakan `-file-line-error` dan `--output-directory=.sumber/.build` agar root bebas berkas sisa dan error menunjuk baris persis:

```powershell
# PowerShell (Windows) / kompatibel alur Linux
New-Item -ItemType Directory -Force -Path ".sumber/.build" | Out-Null
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error --output-directory=.sumber/.build makalah.tex
# Jika memakai BibTeX: bibtex .sumber/.build/makalah (dengan BIBINPUTS=.sumber)
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error --output-directory=.sumber/.build makalah.tex
Copy-Item ".sumber\.build\makalah.pdf" "makalah.pdf" -Force
```

Setelah suntingan selesai, jalankan ulang `tex_index` dengan `--check` untuk menyegarkan `.sumber/INDEX.json` dan memastikan nol pelanggaran LOC, nol berkas yatim, dan nol kebocoran file build di root.
