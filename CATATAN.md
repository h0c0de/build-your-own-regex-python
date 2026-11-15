# CATATAN — Build 5: Regex Engine dengan Python

Mengikuti Project R, *Build Your Own Regular Expression Engines:
Backtracking, NFA, DFA* — https://build-your-own.org/b2a/r0_intro
Satu halaman per irisan: konsep inti + temuan.

## Irisan 1 — Parser (R1) (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab R1 panduan — parser recursive descent yang mengubah string regex menjadi AST bertuple: `None` (kosong), `'dot'`, karakter literal, `('cat', a, b)`, `('split', a, b)`, `('repeat', node, min, max)`. Tiga tingkat fungsi mengikuti tiga presedensi: `parse_split` (alternasi, terendah) → `parse_concat` → `parse_node` + `parse_postfix` (pengulangan, tertinggi).

**Bukti jalan:** `uji_irisan1.py` — 29/29 PASS pada jalan pertama. Bagian A adalah assert milik panduan itu sendiri, apa adanya; Bagian B membuktikan presedensi (`ab*` = a lalu b*, bukan (ab)*), asosiatif kiri kedua operator infix, kurung yang mengalahkan presedensi, postfix di atas grup, dan cabang alternasi kosong `(a|)` yang sah; Bagian C memeriksa kedelapan jalur kesalahan (kurung tak seimbang, `*` tanpa sasaran, `{2,1}`, kurung kurawal tak tertutup, dsb.).

**Konsep inti:**
- Parsing regex tidak butuh teori besar: satu fungsi per tingkat presedensi, dan operator berprioritas tertinggi justru diurai di tingkat terdalam. Konkatenasi yang "tak terlihat" diperlakukan persis seperti operator perkalian implisit dalam rumus.
- AST adalah kontrak antar-irisan: tiga mesin berikutnya (backtracking, NFA, DFA) tidak pernah menyentuh string pola lagi — semuanya bekerja di atas pohon yang sama. Parser yang benar hari ini berarti tiga mesin mewarisi kebenaran itu.
- Catatan kecil: panduan menyebut konstanta `RE_REPEAT_LIMIT` tanpa memberi nilainya; kami tetapkan 1000 dan mencantumkannya sebagai keputusan kami, bukan angka panduan.

## Irisan 2 — Backtracking (R2) (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab R2 panduan — `match_backtrack`, sebuah generator yang dari satu posisi menghasilkan *semua* posisi akhir yang bisa dicapai subpohon AST. Konkatenasi meminta kandidat subpohon pertama satu per satu dan mencoba melanjutkannya (mundur = meminta kandidat berikutnya — itulah backtracking, tanpa tumpukan manual berkat `yield`). Pengulangan ditampung lalu dibalik agar kandidat paling rakus keluar lebih dulu, dan posisi duplikat disaring dengan set seperti catatan panduan.

**Bukti jalan:** `uji_irisan2.py` — semua hijau pada jalan pertama: 31 kasus kurasi (masing-masing dikontrol silang ke `re` agar harapannya sendiri tidak salah), sifat rakus terbukti persis (`a*` atas "aaa" menghasilkan kandidat 3, 2, 1, 0 berurutan), dan **uji diferensial acak: 2.400 pasangan pola/teks yang dibangkitkan dari tata bahasa subset yang sama — nol perbedaan vonis dengan `re.fullmatch`**. Kasus tepi yang biasanya membunuh backtracker naif — `(a*)*` dan cabang kosong `(a|)*b` — lolos.

**Konsep inti:**
- Backtracking adalah pencarian yang ditulis sebagai generator: setiap subekspresi menawarkan daftar kandidat, dan kegagalan di hilir cukup meminta kandidat berikutnya. Kode mesinnya pendek justru karena Python yang memegang tumpukan mundurnya.
- Kelemahannya sudah terlihat dari bentuknya: kandidat yang sama dapat dihitung berulang lewat jalan berbeda — hari ini belum terasa pada teks 6 huruf, tapi pola bersarang seperti `(a+)+$` akan meledakkannya (dibuktikan kuantitatif di Irisan 4, dan itulah alasan dua mesin berikutnya ada).
- TODO panduan sendiri kami warisi dengan sadar: pengulangan atas subekspresi yang cocok-kosong berputar sampai batas 1000 tanpa kemajuan — boros tapi berhenti, dan vonisnya tetap benar.

## Irisan 3 — NFA (R3) (15 Nov 2026, terverifikasi)

**Yang dibangun:** bab R3 panduan — AST dikompilasi ke graf (konstruksi ala Thompson): simpul berupa daftar tautan bersyarat, `None` = tautan bebas/epsilon. Simulasi memelihara *himpunan* keadaan dan melangkah per karakter (`nfa_step` memakan karakter, `nfa_expand` menutup himpunan lewat tautan bebas). Pengulangan terbatas `{x,y}` — yang tidak bisa diungkapkan graf biasa — ditangani simpul khusus "boss" dengan penghitung yang menempel pada keadaan: keadaan simulasi adalah `(id_simpul, kv)` dengan `kv` tuple terurut berisi hitungan tiap boss yang sedang aktif.

**Bukti jalan:** `uji_irisan3.py` — semua hijau pada jalan pertama: baterai kurasi diperluas (termasuk `a{0}`, batas-batas `{3,6}`, dan **boss bersarang** `(a{2}){3}`), dan diferensial acak kini *tiga arah* — NFA == backtracking == `re` pada 2.400 pasangan yang sama dengan Irisan 2, beda = 0. Regresi Irisan 1–2 hijau.

**Konsep inti:**
- Perbedaan kedua mesin adalah cara memecah masalah: backtracking memecah *pola* menjadi subekspresi dan mencarinya mendalam (DFS); NFA memecah *teks* menjadi langkah-langkah dan menjalani semua posisi yang mungkin serentak (BFS). Karena semua jalan hidup bersama dalam satu himpunan, tidak ada jalan yang dihitung dua kali — duplikasi yang menjadi penyakit backtracking lenyap secara struktural, bukan dioptimalkan.
- Harga yang dibayar: keadaan menjadi lebih kaya (penghitung boss menempel sebagai kv) dan mesin tidak lagi tahu kecocokan "paling rakus" — untuk vonis cocok/tidak (fullmatch), itu memang tidak relevan.
- Boss bersarang membuktikan desain kv-nya: dua penghitung dari dua boss berbeda hidup berdampingan dalam satu keadaan tanpa saling menimpa, karena kuncinya adalah identitas door_in masing-masing boss.

## Irisan 4 — DFA + final (15 Nov 2026, terverifikasi)

**Yang dibangun:** DFA lewat konstruksi subset di atas NFA Irisan 3: satu keadaan DFA adalah frozenset keadaan NFA yang sudah ditutup epsilon; transisi dihitung malas per (keadaan, karakter) lalu di-cache, sehingga setiap karakter teks menelan tepat satu langkah tabel. *Catatan kejujuran:* bab R4 panduan tercantum di halaman intro **tanpa tautan** — tidak terbit sebagai bab yang bisa dibaca — jadi DFA ini konstruksi subset buku-teks standar di atas NFA kami sendiri, bukan penyalinan bab panduan.

**Bukti jalan:** `uji_irisan4.py` — diferensial kini **empat arah** (backtracking == NFA == DFA == `re`) pada baterai kurasi dan 2.400 pasangan acak yang sama: beda = 0. Regresi Irisan 1–3 hijau. Ketiga mesin terbukti setara secara vonis.

**Temuan terbesar build ini — ledakan yang tidak terjadi:** rencana awal mengasumsikan demo buku teks: `(a+)+` melawan `a^n+b` akan meledakkan backtracking secara eksponensial sementara NFA/DFA linear. **Pengukuran membantahnya di kedua arah:**

| n | backtracking | NFA | DFA |
|---|---|---|---|
| 50 | 15 ms | — | — |
| 100 | 112 ms | 948 ms | — |
| 200 | 797 ms | 7.369 ms | 14.733 ms |
| 400 | 7.195 ms | — | — |

- Backtracking tumbuh ±7–9× per penggandaan n — polinomial curam (±n³), **bukan** eksponensial (yang eksponensial tak akan menyelesaikan n=100 sama sekali). Sebabnya struktural: panduan menyaring posisi duplikat di konkatenasi dan memelihara *himpunan* posisi per tingkat pengulangan, sehingga partisi-partisi yang biasanya dihitung berulang menyatu. Desain "brute force" panduan diam-diam sudah setengah NFA.
- Yang paling lambat justru NFA (dan DFA malasnya, yang mewarisi biaya langkah NFA): penghitung boss membuat keadaan yang secara makna sama menjadi berbeda hanya karena hitungannya berbeda — himpunan keadaan terpecah kombinatorial pada pengulangan tak-terbatas bersarang. Biaya desain penghitung itu nyata dan terukur.
- Pada teks jinak panjang (5.003 huruf, pola `(a|b)*abb`) ketiganya sekejap: backtracking malah tercepat (1,7 ms vs NFA 6,4 ms vs DFA 8,0 ms).

**Konsep inti penutup seri:** tiga mesin, satu AST, vonis identik — yang membedakan hanyalah *kapan* pekerjaan dibayar dan *dalam bentuk apa* keadaan disimpan. Dan pelajaran metodologis yang menutup kelima build seri ini dengan pas: klaim kinerja dari buku teks pun harus diukur pada implementasi nyata sebelum dipercaya.
