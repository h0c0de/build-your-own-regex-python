# build-your-own-regex-python

Membangun mesin **regular expression** dari nol dengan Python —
parser, lalu *tiga* mesin pencocok yang berbeda di atas pohon yang
sama: backtracking, NFA, dan DFA. Bagian dari seri
[build-your-own-x](https://github.com/codecrafters-io/build-your-own-x)
(fork: [h0c0de/build-your-own-x](https://github.com/h0c0de/build-your-own-x)).

Panduan: Project R, *Build Your Own Regular Expression Engines:
Backtracking, NFA, DFA* — https://build-your-own.org/b2a/r0_intro
(R1 parsing, R2 backtracking, R3 NFA). Bab R4 (DFA) tercantum di
halaman intro panduan tanpa tautan; DFA di sini adalah konstruksi
subset buku-teks standar di atas NFA R3 kami sendiri — dicatat apa
adanya di CATATAN.

## Isi

- `mesinregex.py` — parser recursive descent (regex → AST) + ketiga
  mesin: `re_full_match_bt`, `re_full_match_nfa`, `re_full_match_dfa`.
- `uji_irisan1.py` … `uji_irisan4.py` — bukti per irisan; puncaknya
  uji diferensial **empat arah** (ketiga mesin vs modul `re` asli)
  pada 2.400 pasangan pola/teks acak: nol perbedaan.
- `CATATAN.md` — satu halaman per irisan: konsep inti + temuan,
  termasuk temuan kinerja yang berlawanan dengan buku teks (di bawah).
- `RENCANA.md` — rencana irisan & pagar selesai.

## Fitur regex

Literal, `.`, konkatenasi, alternasi `|`, pengulangan `*`, `+`,
`{n}`, `{x,}`, `{x,y}`, subekspresi `(...)`. Di luar cakupan panduan:
kelas karakter `[...]`, jangkar, escape, grup non-capturing.

## Temuan kinerja utama (terukur, bukan asumsi)

Pola jahat klasik `(a+)+` melawan `a^n + b`:

| n | backtracking | NFA | DFA |
|---|---|---|---|
| 100 | 112 ms | 948 ms | — |
| 200 | 797 ms | 7.369 ms | 14.733 ms |
| 400 | 7.195 ms | — | — |

Backtracking panduan **tidak meledak eksponensial** — dedup posisi di
konkatenasi dan himpunan posisi per tingkat pengulangan membuatnya
tumbuh polinomial curam (±n³). Yang justru paling lambat adalah NFA:
penghitung "boss" untuk pengulangan memecah himpunan keadaan menjadi
sangat banyak keadaan berbeda. Pelajarannya: jangan hafalkan vonis
buku teks — ukur implementasi nyatanya.

## Cara menjalankan

```sh
python3 uji_irisan1.py   # parser
python3 uji_irisan2.py   # backtracking vs re
python3 uji_irisan3.py   # NFA, diferensial tiga arah
python3 uji_irisan4.py   # DFA, diferensial empat arah + pengukuran
```

Python ≥ 3.10, pustaka standar saja.
