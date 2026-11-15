"""디디콩 레이싱(JP v79) ROM 의 일본어(0x80 xx 2바이트) 문자열 훑기 → work/jp_scan.json + 구역별 분량"""
import re, struct, json, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = r'C:/claude/roms/n64/Diddy Kong Racing (Japan).z64'
d = open(ROM, 'rb').read()
src = open(os.path.join(ROOT, 'ref', 'dkrText.cpp'), encoding='utf-8').read()
body = src[src.index('DKRJP_FONT_CHARACTERS'):]; body = body[body.index('{') + 1:body.index('};')]
body = '\n'.join(l.split('//')[0] for l in body.splitlines())
import ast
tbl = ast.literal_eval('[' + body + ']')                # C 문자열 표기 = 파이썬 문자열 표기
assert len(tbl) == 256, len(tbl)
B = 0xEE5D0; n = struct.unpack_from('>I', d, B)[0]; v = struct.unpack_from('>%dI' % (n + 1), d, B + 4); base = B + 4 + 4 * (n + 1)
sec = lambda o: max([i for i in range(n) if base + v[i] <= o], default=-1)
per = {}
for m in re.finditer(rb'(?:\x80[\x00-\xff]|[\x20-\x7e\n])*(?:\x80[\x00-\xff]){2,}(?:\x80[\x00-\xff]|[\x20-\x7e\n])*', d):
    g = m.group(); s = ''; i = 0
    while i < len(g):
        if g[i] == 0x80 and i + 1 < len(g): s += tbl[g[i + 1]]; i += 2
        else: s += chr(g[i]); i += 1
    per.setdefault(sec(m.start()), []).append((hex(m.start()), s))
tot = 0
for k in sorted(per):
    c = sum(len(s) for _, s in per[k]); tot += c
    print(k, hex(base + v[k]) if k >= 0 else 'code', len(per[k]), '줄', c, '자 |', per[k][0][1][:24], '|', per[k][-1][1][:24])
print('합계', tot, '자')
json.dump({str(k): per[k] for k in per}, open(os.path.join(ROOT, 'work', 'jp_scan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
