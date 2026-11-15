# uji_irisan4.py — Bukti Irisan 4: DFA + pengukuran kinerja + final.
# A: diferensial EMPAT arah (bt, nfa, dfa, re) pada baterai + 2.400 acak.
# B: kinerja TERUKUR pada pola jahat klasik (a+)+ — hasilnya TIDAK
#    seperti buku teks, dan uji ini menegaskan apa yang benar-benar
#    terjadi pada implementasi panduan (lihat CATATAN Irisan 4):
#    backtracking tumbuh polinomial curam (~n^3), BUKAN eksponensial,
#    berkat dedup posisi; NFA justru paling lambat di pola ini karena
#    penghitung boss memecah himpunan keadaan.
# C: regresi Irisan 1-3.

import random
import re
import subprocess
import sys
import time
import os

from mesinregex import (DFA, re_full_match_bt, re_full_match_dfa,
                        re_full_match_nfa, re_parse)

gagal = []


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


KASUS = [
    ('abc', 'abc', True), ('abc', 'abd', False),
    ('a|b', 'b', True), ('a*', 'aaa', True), ('a*', 'aab', False),
    ('a{2,3}', 'aaaa', False), ('a{2,3}', 'aaa', True),
    ('(a|b)*', 'abba', True), ('(a|b)*', 'abca', False),
    ('a(b|c)*d', 'abcbd', True), ('(a*)*', 'aaa', True),
    ('(a{2}){3}', 'aaaaaa', True), ('(a{2}){3}', 'aaaa', False),
    ('', '', True), ('(a+)+', 'aaaa', True), ('(a+)+', 'aaab', False),
]
for pola, teks, harap in KASUS:
    node = re_parse(pola)
    hasil = (re_full_match_bt(node, teks), re_full_match_nfa(node, teks),
             re_full_match_dfa(node, teks), bool(re.fullmatch(pola, teks)))
    cek(f'empat arah {pola!r} ~ {teks!r}', hasil == (harap,) * 4, str(hasil))

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


beda = total = 0
for _ in range(300):
    pola = pola_acak()
    node = re_parse(pola)
    dfa = DFA(node)
    for _ in range(8):
        teks = ''.join(random.choice(HURUF) for _ in range(random.randint(0, 6)))
        total += 1
        vonis = bool(re.fullmatch(pola, teks))
        if not (re_full_match_bt(node, teks) == re_full_match_nfa(node, teks)
                == dfa.full_match(teks) == vonis):
            beda += 1
            if beda <= 5:
                print('  BEDA:', repr(pola), repr(teks))
cek(f'diferensial acak empat arah {total} pasangan', beda == 0, f'beda={beda}')

# --- B: kinerja terukur pada pola jahat klasik ---
print()
print('Pengukuran: pola (a+)+ , teks = "a"*n + "b" (tidak akan cocok)')
node_ledak = re_parse('(a+)+')


def ukur(fn, *a):
    t0 = time.perf_counter()
    fn(*a)
    return time.perf_counter() - t0


t60 = ukur(re_full_match_bt, node_ledak, 'a' * 60 + 'b')
t120 = ukur(re_full_match_bt, node_ledak, 'a' * 120 + 'b')
t120_nfa = ukur(re_full_match_nfa, node_ledak, 'a' * 120 + 'b')
print(f'  bt  n=60 : {t60 * 1000:8.1f}ms')
print(f'  bt  n=120: {t120 * 1000:8.1f}ms  (rasio {t120 / t60:.1f}x per 2x huruf)')
print(f'  nfa n=120: {t120_nfa * 1000:8.1f}ms')
cek('backtracking tumbuh curam (rasio n=120/60 > 3x)', t120 / t60 > 3,
    f'{t120 / t60:.1f}x')
cek('tapi BUKAN eksponensial: n=120 selesai < 5 dtk '
    '(eksponensial sejati tak akan selesai sama sekali)', t120 < 5,
    f'{t120:.2f}s')
cek('NFA lebih lambat dari backtracking pada pola ini '
    '(penghitung boss memecah keadaan)', t120_nfa > t120,
    f'nfa {t120_nfa * 1000:.0f}ms vs bt {t120 * 1000:.0f}ms')

# --- C: regresi ---
for nm in ('uji_irisan1.py', 'uji_irisan2.py', 'uji_irisan3.py'):
    rr = subprocess.run(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), nm)],
                        capture_output=True, timeout=300)
    cek(f'regresi {nm}', rr.returncode == 0)

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 4 terbukti: DFA setara; kinerja terukur, bukan asumsi.')
