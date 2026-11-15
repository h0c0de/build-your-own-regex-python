# RENCANA — Build 5: Regex Engine dengan Python

Sumber: daftar build-your-own-x (fork h0c0de), seksi "Build your own
`Regex Engine`", entri Python:

- *Build Your Own Regular Expression Engines: Backtracking, NFA, DFA* —
  Project R di build-your-own.org: https://build-your-own.org/b2a/r0_intro
  (R1 parsing, R2 backtracking, R3 NFA via graph traversal, R4 DFA)

Dipilih Vero 15 Nov 2026 (rekomendasi Muse). Satu berkas `mesinregex.py`,
Python murni pustaka standar. Wasit pembanding: modul `re` bawaan Python
— uji diferensial pola/teks melawan `re` adalah final yang tidak bisa
dipalsukan.

## Himpunan fitur (dari panduan R1)

Literal, `.` (karakter apa pun), konkatenasi `ab`, alternasi `a|b`,
pengulangan `a*`, `a+`, `a{n}`, `a{x,}`, `a{x,y}`, subekspresi `(a)`.
AST: `None` (kosong), `'dot'`, karakter, `('cat', a, b)`,
`('split', a, b)`, `('repeat', node, min, max)`.

Di luar cakupan panduan (dicatat, bukan disembunyikan): kelas karakter
`[...]`, jangkar `^$`, escape `\d` dsb., grup non-capturing, lazy quantifier.

## Irisan

- [x] Irisan 1 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md). Parser (R1): recursive descent tiga tingkat
      (split → concat → node+postfix). Uji: assert milik panduan sendiri
      + presedensi operator + sarang kurung + semua jalur kesalahan.
- [x] Irisan 2 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md). Mesin backtracking (R2): eksekusi AST secara rekursif.
      Uji diferensial awal vs `re.fullmatch` pada baterai pola/teks.
- [x] Irisan 3 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md). NFA (R3): kompilasi AST ke graf keadaan (konstruksi
      Thompson) + simulasi traversal. Uji diferensial yang sama harus
      hijau di kedua mesin.
- [x] Irisan 4 — selesai & terverifikasi 15 Nov 2026 (lihat CATATAN.md). DFA (R4) + final: konstruksi subset NFA→DFA; pengukuran
      kinerja `(a+)+` membantah asumsi ledakan eksponensial (hasil
      sebenarnya tercatat di CATATAN); uji diferensial empat arah
      2.400 pasangan; tutup + terbit.

## Pagar selesai

- [x] Tiga mesin terbukti oleh uji diferensial melawan `re`.
- [x] `CATATAN.md` satu halaman per irisan: konsep inti + temuan.
- [ ] Repo GitHub publik `build-your-own-regex-python` terbit & terverifikasi.
