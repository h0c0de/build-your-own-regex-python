# uji_irisan2.py — Bukti Irisan 2: backtracking == re.fullmatch.
# Tiga lapis: kasus kurasi tangan, sifat rakus (greedy), lalu uji
# diferensial acak — pola & teks dibangkitkan dari tata bahasa subset
# yang sama, vonis mesin kami dibandingkan dengan modul re asli.

import random
import re
import sys

from mesinregex import match_backtrack, re_full_match_bt, re_parse

gagal = []


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


def cocok(pola, teks):
    return re_full_match_bt(re_parse(pola), teks)


# --- A: kurasi ---
KASUS = [
    ('abc', 'abc', True), ('abc', 'abd', False), ('abc', 'ab', False),
    ('a|b', 'a', True), ('a|b', 'b', True), ('a|b', 'c', False),
    ('a*', '', True), ('a*', 'aaa', True), ('a*', 'aab', False),
    ('a+', '', False), ('a+', 'aaa', True),
    ('a{2,3}', 'a', False), ('a{2,3}', 'aa', True),
    ('a{2,3}', 'aaa', True), ('a{2,3}', 'aaaa', False),
    ('a{2}', 'aa', True), ('a{2,}', 'aaaaa', True),
    ('.', 'x', True), ('..', 'xy', True), ('..', 'x', False),
    ('(ab)+', 'abab', True), ('(ab)+', 'aba', False),
    ('(a|b)*', 'abba', True), ('(a|b)*', 'abca', False),
    ('a(b|c)*d', 'abcbd', True), ('a(b|c)*d', 'ad', True),
    ('a(b|c)*d', 'abx', False),
    ('', '', True), ('', 'a', False),
    ('(a*)*', 'aaa', True), ('(a*)*', '', True),      # pengulangan atas pengulangan kosong
    ('(a|)*b', 'aab', True),                          # cabang kosong di dalam bintang
    ('colou?r', 'color', None),                       # '?' di luar himpunan fitur: JANGAN dipakai
]
for pola, teks, harap in KASUS:
    if harap is None:
        continue
    got = cocok(pola, teks)
    cek(f'bt {pola!r} ~ {teks!r}', got == harap, f'dapat {got}')
    cek(f're {pola!r} ~ {teks!r} (kontrol)', bool(re.fullmatch(pola, teks)) == harap)

# --- B: greedy — kandidat pertama repeat adalah yang terpanjang ---
cek('a* atas "aaa" menghasilkan 3 lebih dulu',
    next(match_backtrack(re_parse('a*'), 'aaa', 0)) == 3)
cek('a* atas "aaa" menghasilkan semua kandidat 3,2,1,0',
    list(match_backtrack(re_parse('a*'), 'aaa', 0)) == [3, 2, 1, 0])

# --- C: diferensial acak vs re ---
random.seed(20261115)
HURUF = 'ab'


def pola_acak(dalam=0):
    pilihan = ['huruf', 'dot'] + (['cat', 'split', 'grup'] if dalam < 3 else [])
    jenis = random.choice(pilihan + ['ulang'] if dalam < 3 else pilihan)
    if jenis == 'huruf':
        return random.choice(HURUF)
    if jenis == 'dot':
        return '.'
    if jenis == 'cat':
        return pola_acak(dalam + 1) + pola_acak(dalam + 1)
    if jenis == 'split':
        return pola_acak(dalam + 1) + '|' + pola_acak(dalam + 1)
    if jenis == 'grup':
        return '(' + pola_acak(dalam + 1) + ')'
    dasar = pola_acak(dalam + 1)
    if len(dasar) > 1:
        dasar = '(' + dasar + ')'
    return dasar + random.choice(['*', '+', '{2}', '{1,2}', '{0,2}'])


beda = 0
total = 0
for _ in range(300):
    pola = pola_acak()
    node = re_parse(pola)
    for _ in range(8):
        teks = ''.join(random.choice(HURUF) for _ in range(random.randint(0, 6)))
        total += 1
        if re_full_match_bt(node, teks) != bool(re.fullmatch(pola, teks)):
            beda += 1
            if beda <= 5:
                print('  BEDA:', repr(pola), repr(teks))
cek(f'diferensial acak {total} pasangan pola/teks', beda == 0, f'beda={beda}')

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 2 terbukti: backtracking setara re pada baterai + acak.')
