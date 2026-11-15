# probe_ledak.py — satu pengukuran per proses: argv = pola teks n mesin
import sys
import time

from mesinregex import DFA, re_full_match_bt, re_full_match_nfa, re_parse

pola, n, mesin = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if pola == '(a+)+':
    teks = 'a' * n + 'b'
elif pola == '(a*)*b':
    teks = 'a' * n
elif pola == '(a|b)*abb':
    import random
    random.seed(7)
    teks = ''.join(random.choice('ab') for _ in range(n)) + 'abb'
else:
    raise SystemExit('pola tak dikenal')

node = re_parse(pola)
t0 = time.perf_counter()
if mesin == 'bt':
    hasil = re_full_match_bt(node, teks)
elif mesin == 'nfa':
    hasil = re_full_match_nfa(node, teks)
else:
    hasil = DFA(node).full_match(teks)
print(f'{pola} n={n} {mesin}: {(time.perf_counter() - t0) * 1000:.1f}ms hasil={hasil}', flush=True)
