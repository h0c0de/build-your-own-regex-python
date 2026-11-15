"""mesinregex — mesin regex dari nol, mengikuti Project R build-your-own.org.

Irisan 1 (R1): parser recursive descent regex -> AST.
Bentuk AST (dari panduan):
  None                  pola kosong
  'dot'                 .  (karakter apa pun)
  'a'                   karakter literal (string 1 huruf)
  ('cat', a, b)         konkatenasi
  ('split', a, b)       alternasi
  ('repeat', x, lo, hi) pengulangan lo..hi (hi bisa inf)

Presedensi: postfix (* + {..}) tertinggi, lalu konkatenasi, lalu |.
Parser diturunkan per tingkat presedensi: parse_split memanggil
parse_concat, yang memanggil parse_node, yang memanggil parse_postfix.
"""

RE_REPEAT_LIMIT = 1000  # batas pengulangan minimum; panduan menyebut
                        # konstanta ini tanpa memberi nilainya


def parse_int(r, idx):
    save = idx
    while idx < len(r) and r[idx].isdigit():
        idx += 1
    return idx, int(r[save:idx]) if save != idx else None


def parse_postfix(r, idx, node):
    """a*, a+, a{x}, a{x,}, a{x,y} — operator postfix sesudah satu node."""
    if idx == len(r) or r[idx] not in '*+{':
        return idx, node
    ch = r[idx]
    idx += 1
    if ch == '*':
        rmin, rmax = 0, float('inf')
    elif ch == '+':
        rmin, rmax = 1, float('inf')
    else:
        idx, i = parse_int(r, idx)
        if i is None:
            raise Exception('expect int')
        rmin = rmax = i
        if idx < len(r) and r[idx] == ',':
            idx, j = parse_int(r, idx + 1)
            rmax = j if (j is not None) else float('inf')
        if idx < len(r) and r[idx] == '}':
            idx += 1
        else:
            raise Exception('unbalanced brace')
    if rmax < rmin:
        raise Exception('min repeat greater than max repeat')
    if rmin > RE_REPEAT_LIMIT:
        raise Exception('the repetition number is too large')
    return idx, ('repeat', node, rmin, rmax)


def parse_node(r, idx):
    """Satu elemen: karakter, '.', atau subekspresi (...); lalu postfix."""
    ch = r[idx]
    idx += 1
    assert ch not in '|)'
    if ch == '(':
        idx, node = parse_split(r, idx)
        if idx < len(r) and r[idx] == ')':
            idx += 1
        else:
            raise Exception('unbalanced parenthesis')
    elif ch == '.':
        node = 'dot'
    elif ch in '*+{':
        raise Exception('nothing to repeat')
    else:
        node = ch
    idx, node = parse_postfix(r, idx, node)
    return idx, node


def parse_concat(r, idx):
    """Urutan elemen (konkatenasi implisit), berhenti di | atau )."""
    prev = None
    while idx < len(r):
        if r[idx] in '|)':
            break
        idx, node = parse_node(r, idx)
        prev = node if prev is None else ('cat', prev, node)
    return idx, prev


def parse_split(r, idx):
    """Alternasi: concat (| concat)* — presedensi terendah, tingkat teratas."""
    idx, prev = parse_concat(r, idx)
    while idx < len(r):
        if r[idx] == ')':
            break
        assert r[idx] == '|', 'BUG'
        idx, node = parse_concat(r, idx + 1)
        prev = ('split', prev, node)
    return idx, prev


def re_parse(r):
    idx, node = parse_split(r, 0)
    if idx != len(r):
        raise Exception('unexpected ")"')
    return node


# --------------------------------------- Irisan 2 (R2): backtracking ---
# match_backtrack adalah generator: dari posisi idx ia menghasilkan
# SEMUA posisi akhir yang bisa dicapai subpohon ini. Pemanggil mencoba
# kandidat satu per satu; bila lanjutan gagal, generator diminta
# kandidat berikutnya — itulah backtracking, tanpa tumpukan manual.

def match_backtrack(node, text, idx):
    if node is None:
        yield idx  # pola kosong cocok tanpa memakan karakter
    elif node == 'dot':
        if idx < len(text):
            yield idx + 1
    elif isinstance(node, str):
        assert len(node) == 1
        if idx < len(text) and text[idx] == node:
            yield idx + 1
    elif node[0] == 'cat':
        yield from match_backtrack_concat(node, text, idx)
    elif node[0] == 'split':
        yield from match_backtrack(node[1], text, idx)
        yield from match_backtrack(node[2], text, idx)
    elif node[0] == 'repeat':
        yield from match_backtrack_repeat(node, text, idx)
    else:
        assert not 'reachable'


def match_backtrack_concat(node, text, idx):
    met = set()
    for idx1 in match_backtrack(node[1], text, idx):
        if idx1 in met:
            continue  # posisi duplikat: jangan kerjakan dua kali
        met.add(idx1)
        yield from match_backtrack(node[2], text, idx1)


def match_backtrack_repeat(node, text, idx):
    _, sub, rmin, rmax = node
    rmax = min(rmax, RE_REPEAT_LIMIT)
    output = []  # ditampung lalu dibalik: yang paling rakus lebih dulu
    if rmin == 0:
        output.append(idx)
    start = {idx}
    for i in range(1, rmax + 1):
        found = set()
        for idx1 in start:
            for idx2 in match_backtrack(sub, text, idx1):
                found.add(idx2)
                if i >= rmin:
                    output.append(idx2)
        # Catatan panduan (TODO mereka): bila satu-satunya kecocokan
        # berpanjang nol, loop ini tetap berputar sampai rmax — boros
        # tapi berhenti; diperbaiki tuntas oleh mesin NFA nanti.
        if not found:
            break
        start = found
    yield from reversed(output)


def re_full_match_bt(node, text):
    """True bila AST node mencocokkan SELURUH text (semantik fullmatch)."""
    for idx in match_backtrack(node, text, 0):
        if idx == len(text):
            return True
    return False


# ------------------------------- Irisan 3 (R3): NFA / traversal graf ---
# AST dikompilasi menjadi graf: simpul = list berisi tautan (syarat,
# tujuan); syarat None = tautan bebas (epsilon), 'dot'/karakter =
# tautan yang memakan karakter itu. Pengulangan {x,y} memakai simpul
# khusus "boss" (tuple) yang membawa penghitung: keadaan simulasi
# bukan lagi sekadar simpul, melainkan (id_simpul, kv) dengan kv =
# tuple terurut pasangan (id_door_in, hitungan). Simulasi memelihara
# HIMPUNAN keadaan sekaligus — semua jalan dijelajahi serentak (BFS),
# jadi tidak ada backtracking dan tidak ada pekerjaan duplikat.

def nfa_make(node, start, end, id2node):
    if node is None:
        start.append((None, end))
    elif node == 'dot':
        start.append(('dot', end))
    elif isinstance(node, str):
        start.append((node, end))
    elif node[0] == 'cat':
        middle = []
        id2node[id(middle)] = middle
        nfa_make(node[1], start, middle, id2node)
        nfa_make(node[2], middle, end, id2node)
    elif node[0] == 'split':
        nfa_make(node[1], start, end, id2node)
        nfa_make(node[2], start, end, id2node)
    elif node[0] == 'repeat':
        nfa_make_repeat(node, start, end, id2node)
    else:
        assert not 'reachable'


def nfa_make_repeat(node, start, end, id2node):
    _, sub, rmin, rmax = node
    rmax = min(rmax, RE_REPEAT_LIMIT)
    door_in = []
    door_out = ('boss', door_in, end, rmin, rmax)
    id2node[id(door_in)] = door_in
    id2node[id(door_out)] = door_out
    nfa_make(sub, door_in, door_out, id2node)
    start.append((None, door_in))
    if rmin == 0:
        start.append((None, end))


def kv_increase(kv, key):
    kv = dict(kv)
    val = kv.get(key, 0) + 1
    kv[key] = val
    return tuple(sorted(kv.items())), val


def kv_delete(kv, key):
    return tuple((k, v) for k, v in kv if k != key)


def nfa_boss(node, kv):
    _, door_in, end, rmin, rmax = node
    key = id(door_in)
    kv, cnt = kv_increase(kv, key)
    if cnt < rmax:
        yield (door_in, kv)              # putar sekali lagi
    if rmin <= cnt <= rmax:
        yield (end, kv_delete(kv, key))  # keluar, penghitung dibuang


def nfa_expand(node_set, id2node):
    """Tutup himpunan keadaan lewat tautan bebas & simpul boss."""
    start = list(node_set)
    while start:
        new_nodes = []
        for node_id, kv in start:
            node = id2node[node_id]
            if isinstance(node, tuple) and node[0] == 'boss':
                node_set.remove((node_id, kv))
                for dst, kv2 in nfa_boss(node, kv):
                    new_nodes.append((id(dst), kv2))
            else:
                for cond, dst in node:
                    if cond is None:
                        new_nodes.append((id(dst), kv))
        start = []
        for state in new_nodes:
            if state not in node_set:
                node_set.add(state)
                start.append(state)


def nfa_step(node_set, ch, id2node):
    """Konsumsi satu karakter: himpunan keadaan berikutnya."""
    assert len(ch) == 1
    next_nodes = set()
    for node_id, kv in node_set:
        node = id2node[node_id]
        assert not isinstance(node, tuple), 'unexpected boss'
        for cond, dst in node:
            if cond == 'dot' or cond == ch:
                next_nodes.add((id(dst), kv))
    return next_nodes


def re_full_match_nfa(node, text):
    """True bila AST node mencocokkan SELURUH text, via simulasi NFA."""
    start, end = [], []
    id2node = {id(start): start, id(end): end}
    nfa_make(node, start, end, id2node)
    node_set = {(id(start), ())}
    nfa_expand(node_set, id2node)
    for ch in text:
        node_set = nfa_step(node_set, ch, id2node)
        nfa_expand(node_set, id2node)
    return (id(end), ()) in node_set


# --------------------- Irisan 4 (R4): DFA via konstruksi subset -------
# Catatan kejujuran: di halaman intro Project R, bab R4 tercantum
# TANPA tautan (tidak terbit sebagai bab yang bisa dibaca saat build
# ini dibuat). DFA di sini adalah konstruksi subset buku-teks standar
# di atas NFA Irisan 3 milik kami sendiri: satu keadaan DFA = satu
# himpunan beku (frozenset) keadaan NFA yang sudah ditutup epsilon.
# Transisi dihitung malas (lazy) per (keadaan, karakter) lalu di-cache:
# setiap karakter teks kemudian menelan tepat SATU langkah tabel —
# tidak ada himpunan yang dihitung ulang, tidak ada mundur.

class DFA:
    def __init__(self, node):
        self.start, self.end = [], []
        self.id2node = {id(self.start): self.start, id(self.end): self.end}
        nfa_make(node, self.start, self.end, self.id2node)
        awal = {(id(self.start), ())}
        nfa_expand(awal, self.id2node)
        self.keadaan_awal = frozenset(awal)
        self.cache = {}

    def langkah(self, keadaan, ch):
        kunci = (keadaan, ch)
        if kunci not in self.cache:
            berikut = nfa_step(set(keadaan), ch, self.id2node)
            nfa_expand(berikut, self.id2node)
            self.cache[kunci] = frozenset(berikut)
        return self.cache[kunci]

    def full_match(self, text):
        keadaan = self.keadaan_awal
        for ch in text:
            keadaan = self.langkah(keadaan, ch)
            if not keadaan:
                return False
        return (id(self.end), ()) in keadaan


def re_full_match_dfa(node, text):
    """True bila AST node mencocokkan SELURUH text, via DFA."""
    return DFA(node).full_match(text)
