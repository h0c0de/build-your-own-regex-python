# uji_irisan1.py — Bukti Irisan 1: parser menghasilkan AST yang benar.
# Bagian A: assert milik panduan R1 itu sendiri, apa adanya.
# Bagian B: presedensi & sarang. Bagian C: semua jalur kesalahan.

import sys

from mesinregex import re_parse

INF = float('inf')
gagal = []


def cek(nama, kondisi, detail=''):
    print(('PASS' if kondisi else 'FAIL'), nama, detail)
    if not kondisi:
        gagal.append(nama)


def sama(pola, harap):
    try:
        got = re_parse(pola)
    except Exception as e:
        cek(f'parse {pola!r}', False, f'pengecualian {e}')
        return
    cek(f'parse {pola!r}', got == harap, f'{got!r}' if got != harap else '')


def salah(pola, potongan):
    try:
        got = re_parse(pola)
    except Exception as e:
        cek(f'error {pola!r}', potongan in str(e), str(e))
        return
    cek(f'error {pola!r}', False, f'malah menghasilkan {got!r}')


# --- A: assert panduan R1 ---
sama('', None)
sama('.', 'dot')
sama('a', 'a')
sama('ab', ('cat', 'a', 'b'))
sama('a|b', ('split', 'a', 'b'))
sama('a+', ('repeat', 'a', 1, INF))
sama('a{3,6}', ('repeat', 'a', 3, 6))
sama('a|bc', ('split', 'a', ('cat', 'b', 'c')))

# --- B: presedensi & bentuk lain ---
sama('a*', ('repeat', 'a', 0, INF))
sama('a{3}', ('repeat', 'a', 3, 3))
sama('a{3,}', ('repeat', 'a', 3, INF))
sama('ab*', ('cat', 'a', ('repeat', 'b', 0, INF)))          # postfix > concat
sama('a|b|c', ('split', ('split', 'a', 'b'), 'c'))           # split asosiatif kiri
sama('abc', ('cat', ('cat', 'a', 'b'), 'c'))                 # cat asosiatif kiri
sama('(a|b)c', ('cat', ('split', 'a', 'b'), 'c'))            # kurung mengalahkan presedensi
sama('(ab)+', ('repeat', ('cat', 'a', 'b'), 1, INF))         # postfix atas grup
sama('((a))', 'a')                                          # kurung bersarang larut
sama('a(b|c)*d', ('cat', ('cat', 'a', ('repeat', ('split', 'b', 'c'), 0, INF)), 'd'))
sama('.', 'dot')
sama('.*', ('repeat', 'dot', 0, INF))
sama('(a|)', ('split', 'a', None))                           # cabang kosong sah

# --- C: kesalahan ---
salah('(a', 'unbalanced parenthesis')
salah('a)', 'unexpected ")"')
salah('*a', 'nothing to repeat')
salah('+', 'nothing to repeat')
salah('a{2,1}', 'min repeat greater than max repeat')
salah('a{', 'expect int')
salah('a{2', 'unbalanced brace')
salah('a{1001}', 'the repetition number is too large')

print()
if gagal:
    print('GAGAL:', ', '.join(gagal))
    sys.exit(1)
print('SEMUA PASS — Irisan 1 terbukti: parser R1 setia & presedensi benar.')
