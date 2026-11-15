# 영문판 원문 전부 뽑기 → /mnt/c/claude/project/dkr-kr-patch/work/kr/en_source.tsv
# 열: id \t 종류 \t 원문(줄바꿈·탭 이스케이프) \t 참고(글꼴/상자)
import json, glob, os, re

V = '/root/dkr_orig/assets/.vanilla/us.v80/'
if not os.path.isdir(V):
    V = '/root/dkr/assets/.vanilla/us.v80/'
OUT = '/mnt/c/claude/project/dkr-kr-patch/work/kr/en_source.tsv'
rows = []


def esc(s):
    return s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')


# 1) 메뉴 글
menu = json.load(open(V + 'text/menu/english_menu_text_v79.json'))['sections']
for k, v in menu.items():
    rows.append(('menu:' + k, 'menu', v, ''))

# 2) 안내 상자(Textbox) 대사 — 영어 = 0~84
TB = V + 'text/game/unknown/'


def tb_file(i):
    for n in ('asset_game_text_%d.json' % i, 'asset_game_text_%d_v79.json' % i):
        if os.path.exists(TB + n):
            return n
    return None


def parse_dialog(b):
    """Dialog(자막) 바이너리 → [(머리8, 문자열 bytes, 구분자 bytes)]"""
    recs = []
    p = 0
    while p < len(b) and b[p] != 0:
        head = b[p:p + 8]
        p += 8
        q = p
        while b[q] != 0:
            q += 2 if b[q] & 0x80 else 1
        s = b[p:q]
        p = q + 1
        sep = b''
        if p < len(b) and b[p] in (10, 12):
            sep = b[p:p + 1]
            p += 1
        recs.append((head, s, sep))
    tail = b[p:]
    return recs, tail


for i in range(85):
    n = tb_file(i)
    if n is None:
        continue
    d = json.load(open(TB + n))
    if d.get('text-type') == 'Dialog':
        b = open(TB + d['raw'], 'rb').read()
        recs, tail = parse_dialog(b)
        for j, (h, s, sep) in enumerate(recs):
            rows.append(('dlg:%d:%d' % (i, j), 'subtitle', s.decode('latin-1'), 'font=%d flags=%d time=%d sep=%s' % (h[5], h[6], h[7], sep.hex())))
        continue
    font = 'FunFont'
    for pi, page in enumerate(d['pages']):
        for ci, c in enumerate(page):
            if c['command'] == 'SetFont':
                font = c['value']
            if c['command'] == 'SetBorder':
                bd = c['value']
            if c['command'] == 'Text':
                rows.append(('tb:%d:%d:%d' % (i, pi, ci), 'textbox', c['value'], font))

# 3) 코스 이름
for f in sorted(glob.glob(V + 'levels/headers/*.json')):
    d = json.load(open(f))
    nm = d.get('name')
    if isinstance(nm, dict) and nm.get('LANGUAGE_ENGLISH'):
        rows.append(('lvl:' + os.path.basename(f), 'level', nm['LANGUAGE_ENGLISH'], ''))

with open(OUT, 'w', encoding='utf-8') as o:
    for r in rows:
        o.write('\t'.join(esc(x) for x in r) + '\n')
print(len(rows), 'rows', os.path.getsize(OUT), 'bytes')
