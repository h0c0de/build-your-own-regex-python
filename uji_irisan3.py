# uji_irisan3.py — Bukti Irisan 3: NFA == backtracking == re.
# Diferensial TIGA arah pada baterai kurasi yang sama dengan Irisan 2
# (termasuk pengulangan terbatas {x,y} yang memakai simpul boss) dan
# pada 2.400 pasangan acak yang sama (benih & pembangkit yang sama).

import random
import re
import sys

from mesinregex import re_full_match_bt, re_full_match_nfa, re_parse

gagal = []


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


KASUS = [
    ('abc', 'abc', True), ('abc', 'abd', False),
    ('a|b', 'b', True), ('a|b', 'c', False),
    ('a*', '', True), ('a*', 'aaa', True), ('a*', 'aab', False),
    ('a+', '', False),
    ('a{2,3}', 'a', False), ('a{2,3}', 'aa', True),
    ('a{2,3}', 'aaa', True), ('a{2,3}', 'aaaa', False),
    ('a{2}', 'aa', True), ('a{2,}', 'aaaaa', True), ('a{2,}', 'a', False),
    ('a{0}', '', True), ('a{0}', 'a', False),
    ('(ab)+', 'abab', True), ('(ab)+', 'aba', False),
    ('(a|b)*', 'abba', True), ('(a|b)*', 'abca', False),
    ('a(b|c)*d', 'abcbd', True), ('a(b|c)*d', 'ad', True),
    ('', '', True), ('', 'a', False),
    ('(a*)*', 'aaa', True), ('(a*)*', '', True),
    ('(a|)*b', 'aab', True),
    ('(a{2}){3}', 'aaaaaa', True), ('(a{2}){3}', 'aaaa', False),  # boss bersarang
    ('x{3,6}', 'xxxx', True), ('x{3,6}', 'xx', False), ('x{3,6}', 'xxxxxxx', False),
]
for pola, teks, harap in KASUS:
    node = re_parse(pola)
    got = re_full_match_nfa(node, teks)
    cek(f'nfa {pola!r} ~ {teks!r}', got == harap, f'dapat {got}')
    cek(f'nfa==bt==re {pola!r} ~ {teks!r}',
        got == re_full_match_bt(node, teks) == bool(re.fullmatch(pola, teks)))

# Diferensial acak tiga arah — benih & pembangkit identik Irisan 2.
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
        vonis = bool(re.fullmatch(pola, teks))
        if re_full_match_nfa(node, teks) != vonis or re_full_match_bt(node, teks) != vonis:
            beda += 1
            if beda <= 5:
                print('  BEDA:', repr(pola), repr(teks))
cek(f'diferensial acak tiga arah {total} pasangan', beda == 0, f'beda={beda}')

# Regresi Irisan 1-2
for n in ('uji_irisan1.py', 'uji_irisan2.py'):
    import subprocess, os
    rr = subprocess.run(['python3', os.path.join(os.path.dirname(os.path.abspath(__file__)), n)],
                        capture_output=True, timeout=120)
    cek(f'regresi {n}', rr.returncode == 0)

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 3 terbukti: NFA setara backtracking & re.')
