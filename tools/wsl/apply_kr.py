# 번역 적용 — ~/dkr 의 에셋·소스에 한글을 써 넣는다(매번 원본 ~/dkr_orig 에서 다시 시작)
import json, os, shutil, re, subprocess, sys

P = '/mnt/c/claude/project/dkr-kr-patch/work/kr/'
O = '/root/dkr_orig/assets/.vanilla/us.v80/'
V = '/root/dkr/assets/.vanilla/us.v80/'
ko = json.load(open(P + 'ko_norm.json', encoding='utf-8'))
charset = [l.rstrip('\n') for l in open(P + 'charset.txt', encoding='utf-8') if l.strip('\n')]
idx = {c: i for i, c in enumerate(charset)}


def enc(s):
    b = bytearray()
    for ch in s:
        o = ord(ch)
        if o < 0x80:
            b.append(o)
        else:
            i = idx[ch]
            b += bytes([0x80 | (i >> 7), 0x80 | (i & 0x7F)])
    return bytes(b)


def restore(rel):
    shutil.copy2(O + rel, V + rel)


def dump(rel, d):
    with open(V + rel, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


n = 0
# 1) 메뉴
rel = 'text/menu/english_menu_text_v79.json'
d = json.load(open(O + rel))
for k in d['sections']:
    d['sections'][k] = ko['menu:' + k]
    n += 1
dump(rel, d)

# 2) 대사 상자 · 자막
TB = 'text/game/unknown/'


def parse_dialog(b):
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
    return recs, b[p:]


for i in range(85):
    rel = None
    for c in ('asset_game_text_%d.json' % i, 'asset_game_text_%d_v79.json' % i):
        if os.path.exists(O + TB + c):
            rel = TB + c
    if rel is None:
        continue
    d = json.load(open(O + rel))
    if d.get('text-type') == 'Dialog':
        braw = TB + d['raw']
        b = open(O + braw, 'rb').read()
        recs, tail = parse_dialog(b)
        out = bytearray()
        for j, (h, s, sep) in enumerate(recs):
            out += h + enc(ko['dlg:%d:%d' % (i, j)]) + b'\0' + sep
            n += 1
        out += tail
        # 원래 바이너리는 4바이트 정렬로 끝난다
        while len(out) % 4:
            out.append(0)
        open(V + braw, 'wb').write(bytes(out))
        restore(rel)
        continue
    for pi, page in enumerate(d['pages']):
        for ci, c in enumerate(page):
            if c['command'] == 'Text':
                c['value'] = ko['tb:%d:%d:%d' % (i, pi, ci)]
                n += 1
    dump(rel, d)

# 3) 코스 이름
for k, v in ko.items():
    if k.startswith('lvl:'):
        rel = 'levels/headers/' + k[4:]
        d = json.load(open(O + rel))
        d['name']['LANGUAGE_ENGLISH'] = v
        dump(rel, d)
        n += 1

# 4) 한글 글꼴(일본어 글꼴 자리)
fd = V + 'fonts/'
shutil.copy2(P + 'kr_font.bin', fd + 'kr_font.bin')
shutil.copy2(P + 'kr_font_table.bin', fd + 'kr_font_table.bin')
jp = json.load(open(O + 'fonts/jp_fonts_v79.json'))
jp['raw-data'] = 'kr_font.bin'
jp['raw-table'] = 'kr_font_table.bin'
dump('fonts/jp_fonts_v79.json', jp)

# 5) 코드 안 문자열(타이틀 연출 캐릭터 이름)
subprocess.check_call(['git', '-C', '/root/dkr', 'checkout', '--', 'src/menu.c'])
mp = '/root/dkr/src/menu.c'
s = open(mp, encoding='latin-1').read()
for k, v in ko.items():
    if k.startswith('code:'):
        en = k[5:]
        lit = '"' + ''.join('\\%03o' % c if c >= 0x80 else chr(c) for c in enc(v)) + '"'
        old = '{ "%s",' % en
        assert s.count(old) == 1, en
        s = s.replace(old, '{ ' + lit + ',')
        n += 1
open(mp, 'w', encoding='latin-1').write(s)
print('적용', n, '줄 · 글자', len(charset))
