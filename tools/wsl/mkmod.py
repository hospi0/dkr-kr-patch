# -*- coding: utf-8 -*-
"""DKR-R(리컴파일 PC 판)용 한글 모드 소스 만들기 (2026-11-15 하스피 «모드 해보자»)
  WSL 에서: python3 mkmod.py  →  /mnt/c/claude/project/dkr-kr-patch/mod/kr/
  · kr_font.c  = 한글판 디컴파일 font.c(~/dkr, patch_src 적용본)에서 글자 함수만 뽑아 전처리한 것
                 render_text_string · get_text_width 를 DKR_REPLACE, 한글 글자 캐시(kr_*)
                 롬 읽기 대신 모드 자원(kr_read_font), mempool 대신 dkr_alloc(kr_alloc)
  · main.c     = SDK 쪽: asset_load / asset_table_load 뒤 훅으로 바뀐 에셋 8개를 한글 자원으로 덮어씀,
                 load_fonts 뒤 한글 캐시 준비, 매 프레임 캐시 나이 줄임, 타이틀 연출 이름 10개 포인터
  · res/a<번호>.bin = 한글판 롬(work/build/dkr_kr.z64)의 바뀐 에셋 묶음 그대로"""
import os, re, struct, subprocess, json

D = '/root/dkr/'
P = '/mnt/c/claude/project/dkr-kr-patch/'
OUT = P + 'mod/kr/'
os.makedirs(OUT + 'res', exist_ok=True)

# ---------- 1) 에셋 자원 ----------
k = open(P + 'work/build/dkr_kr.z64', 'rb').read()
o = open(P + 'work/us/orig_us.z64', 'rb').read()
mp = open(D + 'build/dkr.us.v80.map').read()
KS = int(re.search(r'(0x[0-9a-f]+)\s+__ASSETS_LUT_START', mp).group(1), 16)
KE = int(re.search(r'(0x[0-9a-f]+)\s+__ASSETS_LUT_END', mp).group(1), 16)
n = (KE - KS) // 4
lut = struct.unpack('>%dI' % n, k[KS:KE])
OS_ = o.find(k[KS:KS + 16]); assert OS_ > 0
olut = struct.unpack('>%dI' % n, o[OS_:OS_ + n * 4]); OE = OS_ + n * 4
ASSETS = []
for i in range(lut[0]):
    kb = k[KE + lut[i + 1]:KE + lut[i + 2]]; ob = o[OE + olut[i + 1]:OE + olut[i + 2]]
    if kb != ob:
        open(OUT + 'res/a%d.bin' % i, 'wb').write(kb)
        ASSETS.append((i, len(ob), len(kb)))
print('바뀐 에셋', ASSETS)
WANT = {6, 7, 8, 9, 24, 25, 45, 46}
assert {a[0] for a in ASSETS} == WANT, ASSETS
for i, ol, kl in ASSETS:
    if i in (7, 9, 24):
        assert ol == kl, ('표 크기 다름', i)
    elif i not in (45, 46):
        assert kl <= ol, ('한글 에셋이 원본보다 큼', i, ol, kl)

# ---------- 2) kr_font.c ----------
F = open(D + 'src/font.c').read()
assert 'KR_FONT' in F, 'patch_src 적용본이 아님'


def grab(start_pat, end_pat, text, start_at=0):
    a = text.index(start_pat, start_at)
    b = text.index(end_pat, a)
    return text[a:b]


kr = grab('/* ===== KR_FONT', '\n#endif', F)
kr = kr.replace('mempool_alloc_safe(KR_UNITS * 14 * sizeof(Gfx), COLOUR_TAG_RED)', 'kr_alloc(KR_UNITS * 14 * sizeof(Gfx))')
kr = kr.replace('mempool_alloc_safe(KR_UNITS * sizeof(KrSlot), COLOUR_TAG_RED)', 'kr_alloc(KR_UNITS * sizeof(KrSlot))')
kr = kr.replace('mempool_alloc_safe(KR_UNITS * KR_UNIT_SIZE, COLOUR_TAG_RED)', 'kr_alloc(KR_UNITS * KR_UNIT_SIZE)')
kr = kr.replace('(KrFontHeader *) asset_table_load(ASSET_JAPANESE_FONTS_TABLE)', '(KrFontHeader *) kr_load_table()')
kr = re.sub(r'asset_load\(ASSET_JAPANESE_FONTS, \(u32\) glyph, ([^,]+),\s*h->bytesPerCharacter\);',
            r'kr_read_font(glyph, \1, h->bytesPerCharacter);', kr)
kr = kr.replace('void fontCreateDisplayList(Gfx *dList, Asset46 *asset, s32 width, s32 height);',
                'static void kr_fcdl(Gfx *dList, Asset46 *asset, s32 width, s32 height);')
kr = kr.replace('fontCreateDisplayList(gKrSlots', 'kr_fcdl(gKrSlots')
for bad in ('mempool_alloc_safe', 'asset_table_load', 'asset_load(', 'fontCreateDisplayList'):
    assert bad not in kr, bad
assert 'kr_read_font(glyph' in kr

rts = grab('#if REGION != REGION_JP\nvoid render_text_string(', '\n#else', F)[len('#if REGION != REGION_JP\n'):]
gtw = grab('#if REGION != REGION_JP\ns32 get_text_width(', '\n#else', F)[len('#if REGION != REGION_JP\n'):]
m = re.search(r'#if REGION != REGION_JP\n/\*\*\n \* Official Name: fontCreateDisplayList\n \*/\n(void fontCreateDisplayList.*?\n}\n)', F, re.S)
fcd = m.group(1).replace('void fontCreateDisplayList(', 'static void kr_fcdl(', 1)
assert 'kr_draw_glyph' in rts and 'kr_font_advance' in gtw
rts = rts.replace('get_text_width(', 'kr_get_text_width(')
rts = rts.replace('void render_text_string(', 'void kr_render_text_string(', 1)
gtw = gtw.replace('s32 get_text_width(', 's32 kr_get_text_width(', 1)

head = '\n'.join(l for l in F.split('\n')[:12] if l.startswith('#include')) + '\n'
# 게임 데이터는 고정 주소로(us.v80 전용) — RecompModTool 이 링커 스크립트의 절대 데이터 심볼 재배치를 처리 못 함(SectionAbsolute 로 죽음)
SYM = dict(re.findall(r'^(\w+) = (0x[0-9A-Fa-f]+);', open('/root/modwork/kit-v80/symbols.ld').read() if os.path.exists('/root/modwork/kit-v80/symbols.ld')
                      else open(P + 'ref/dkr-r/modding/reference-us-v80/symbols.ld').read(), re.M))
GV = [('dDialogueBoxBegin', '((Gfx *) %s)'), ('dDialogueBoxDrawModes', '((Gfx (*)[2]) %s)'),
      ('sDialogueBoxIsOpen', '(*(s8 *) %s)'), ('gDescPowsOf10', '((s32 *) %s)'), ('sDialogueBoxDimensions', '((s8 *) %s)'),
      ('gNumberOfFonts', '(*(s32 *) %s)'), ('gFonts', '(*(FontData **) %s)'),
      ('gDialogueBoxBackground', '(*(DialogueBoxBackground **) %s)'), ('gDialogueText', '(*(DialogueTextElement **) %s)'),
      ('gCompactKerning', '(*(s32 *) %s)'), ('sDialogueBoxCloseTimer', '(*(s8 *) %s)')]
gdefs = '\n'.join('#define %s %s' % (nm, fmt % SYM[nm]) for nm, fmt in GV)
# 게임 함수 호출은 SDK dkr_game_call 로(main.c 의 kr_call_dl)
gdefs += '\nvoid kr_call_dl(const char *name, Gfx **dList);'
gdefs += '\n#define rendermode_reset(d) kr_call_dl("rendermode_reset", (d))'
gdefs += '\n#define viewport_scissor(d) kr_call_dl("viewport_scissor", (d))'
src = head + r'''
#define KR_REPLACE __attribute__((used, retain, section(".recomp_patch")))
/* 게임 쪽 font.c 전역 = 고정 주소(SDK reference-us-v80/symbols.ld 값) */
''' + gdefs + r'''
/* main.c(SDK 쪽) */
void *kr_alloc(u32 bytes);
void *kr_load_table(void);
void kr_read_font(void *dst, s32 offset, s32 bytes);
s32 kr_get_text_width(char *text, s32 x, s32 font);

''' + kr + '\n\n' + fcd + '\n' + gtw + '\n\n' + rts + '\n'
open('/tmp/kr_font_src.c', 'w', encoding='utf-8').write(src)
INC = ['-I', '.', '-I', 'include', '-I', 'include/libc', '-I', 'include/PR', '-I', 'include/sys', '-I', 'build', '-I', 'src',
       '-I', 'lib', '-I', 'lib/src', '-I', 'lib/src/gu', '-I', 'lib/src/libc', '-I', 'lib/src/io', '-I', 'lib/src/os']
DEF = ['-D_FINALROM', '-DNDEBUG', '-DTARGET_N64', '-DF3DDKR_GBI', '-DVERSION_US_V80', '-D_MIPS_SZLONG=32',
       '-D_LANGUAGE_C', '-DNON_MATCHING', '-DAVOID_UB']
pp = subprocess.run(['clang', '--target=mips-unknown-none', '-march=mips2', '-mabi=32', '-E', '-P', *DEF, *INC,
                     '/tmp/kr_font_src.c'], cwd=D, capture_output=True, text=True, encoding='utf-8')
if pp.returncode:
    print(pp.stderr[-3000:]); raise SystemExit(1)
open(OUT + 'kr_font.c', 'w', encoding='utf-8').write(
    '/* 자동 생성(tools/wsl/mkmod.py) — 손으로 고치지 말 것 */\n#pragma clang diagnostic ignored "-Weverything"\n' + pp.stdout)
print('kr_font.c', len(pp.stdout))
open(OUT + 'replace.txt', 'w').write('')  # 바꿔치기 없음 — DKR-R 이 두 함수를 보호 함수로 거부 → 시작 훅 + 원래 함수 건너뛰기(main.c)

# ---------- 3) 타이틀 연출 이름 ----------
ko = json.load(open(P + 'work/kr/ko_norm.json', encoding='utf-8'))
cs = [l.rstrip('\n') for l in open(P + 'work/kr/charset.txt', encoding='utf-8') if l.strip('\n')]
idx = {c: i for i, c in enumerate(cs)}


def enc(s):
    b = bytearray()
    for ch in s:
        if ord(ch) < 0x80:
            b.append(ord(ch))
        else:
            c = idx[ch]
            b += bytes([0x80 | (c >> 7), 0x80 | (c & 0x7F)])
    return bytes(b)


ORDER = ['TIMBER', 'BUMPER', 'CONKER', 'TIPTUP', 'DRUMSTICK', 'PIPSY', 'BANJO', 'KRUNCH', 'WIZPIG', 'DIDDY']
menu_c = open(D + 'src/menu.c', encoding='latin-1').read()
seg = menu_c[menu_c.index('gTitleCinematicText[10]'):]
seg = seg[:seg.index('};')]
names = re.findall(r'\{ "((?:[^"\\]|\\.)*)",', seg)
assert len(names) == 10, names
# menu.c 는 한글판(apply_kr) 상태라 8진 이스케이프 — ko_norm 순서로 다시 만듦
title = [enc(ko['code:' + e]) for e in ORDER]
blob = b''.join(t + b'\0' for t in title)
open(OUT + 'res/title.bin', 'wb').write(blob)

import shutil
shutil.copy(P + 'mod/kr_main.c', OUT + 'main.c')

# ---------- 4) mod.toml · dkr.json ----------
open(OUT + 'mod.toml', 'w').write('''[manifest]
id = "dkr_korean"
version = "0.9.0"
display_name = "Korean Translation"
description = "Korean translation of menus, dialogue boxes, subtitles and course names (US v1.1 only)."
authors = ["hospi0"]
game_id = "dkr"
minimum_recomp_version = "1.0.15"
dependencies = []

[build]
sources = ["main.c", "kr_font.c"]
''')
res = {'a%d' % i: 'res/a%d.bin' % i for i in sorted(WANT)}
res['title'] = 'res/title.bin'
json.dump({'schema': 1, 'api': 2, 'activation': 'restart', 'online': 'deterministic', 'development': False,
           'profile': 'large', 'revisions': ['us.v80'],
           'requires': {'core': 1, 'memory': 1, 'resources': 1, 'events': 1, 'game': 1, 'game-hooks': 1},
           'resources': res}, open(OUT + 'dkr.json', 'w'), indent=2)
print('자원', res)
