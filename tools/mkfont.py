# -*- coding: utf-8 -*-
"""디디콩 레이싱(영문판) 한글 글꼴 만들기 — 갈무리 BDF 화소 그대로

입력: work/kr/charset.txt (UTF-8, 한 줄에 한 글자, 줄 번호 = 글자 색인)
출력: work/kr/kr_font.bin (ASSET_JAPANESE_FONTS 자리), work/kr/kr_font_table.bin (머리표 4×16 B)
      work/preview_font_<n>/ 글자판 미리보기(원본 영문 | 한글)

글꼴 번호 = 영문판 글꼴 번호: 0 FunFont · 1 SmallFont · 2 BigFont · 3 SubtitleFont
"""
import os, sys, struct
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from bdf import Font

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GAL = 'C:/claude/utils/font/Galmuri-v2.40.3/'

FMT_RGBA16, FMT_IA8 = 1, 5


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def grad(stops, n):
    """stops = [(위치 0~1, 색)…] → n 줄 색"""
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        for j in range(len(stops) - 1):
            p0, c0 = stops[j]
            p1, c1 = stops[j + 1]
            if p0 <= t <= p1:
                out.append(lerp(c0, c1, (t - p0) / max(1e-9, p1 - p0)))
                break
    return out


# 영문 FunFont 줄 색(실측): 빨강 → 자주 → 보라, 맨 아래 노랑 / 테두리 남색
FUN_GRAD = [(0, (255, 0, 0)), (0.3, (255, 0, 70)), (0.6, (255, 0, 255)), (0.8, (215, 0, 255)), (1.0, (250, 250, 0))]
FUN_EDGE = (15, 31, 63)
# 영문 FunFont 실측(work/us/fontlook/funfont): 몸통 빨강(위) → 자홍(아래), 테두리 1px 연노랑(위) → 노랑(아래), 오른쪽 아래 남색 그림자
FUN_GRAD2 = [(0, (255, 24, 0)), (0.45, (255, 0, 100)), (1.0, (215, 0, 250))]
FUN_EDGE_GRAD = [(0, (250, 250, 200)), (0.5, (245, 240, 110)), (1.0, (240, 240, 16))]
FUN_SHADOW = (14, 26, 64)
# 영문 BigFont 줄 색(실측): 연두 → 노랑 → 주황 → 파랑 / 테두리 파랑, 그림자 검정
BIG_GRAD = [(0, (200, 250, 70)), (0.35, (255, 255, 40)), (0.75, (250, 180, 0)), (1.0, (255, 140, 20))]
BIG_EDGE = (0, 0, 200)

# 칸 폭, 칸 높이, 전진 폭, 줄 위 내림, 형식
SPECS = {
    0: dict(bdf='Galmuri11-Bold', scale=1, cw=16, ch=14, adv=12, yoff=-1, fmt=FMT_RGBA16, outline=1,
            grad=FUN_GRAD2, edge=FUN_EDGE, edge_grad=FUN_EDGE_GRAD, shadow=FUN_SHADOW),   # 영문 FunFont 색 실측(2026-11-15 «일시정지 컬러»)
    1: dict(bdf='Galmuri9', scale=1, cw=16, ch=12, adv=10, yoff=0, fmt=FMT_IA8, outline=0),
    2: dict(bdf='Galmuri11-Bold', scale=2, cw=32, ch=28, adv=24, yoff=0, fmt=FMT_RGBA16, outline=2,
            grad=BIG_GRAD, edge=BIG_EDGE, shadow=True,
            ttf=('C:/claude/utils/font/nanum-gothic/NanumGothicExtraBold.ttf', 24, 110)),   # 원래 크기로 그림(2026-11-15 하스피 «큰 폰트 저해상도» → 나눔고딕 ExtraBold)
    3: dict(bdf='Galmuri11-Bold', scale=1, cw=16, ch=14, adv=12, yoff=1, fmt=FMT_IA8, outline=0),
}

_fonts = {}


def bdf(name):
    if name not in _fonts:
        _fonts[name] = Font(GAL + name + '.bdf')
    return _fonts[name]


_ttf = {}


def ttf_ink(ch, spec):
    """벡터 글꼴을 원래 크기로 그려 문턱값(1비트) — 한글 «가» 잉크 맨 위 = 0"""
    from PIL import ImageDraw, ImageFont
    path, size, thr = spec['ttf']
    if path not in _ttf:
        font = ImageFont.truetype(path, size)
        im = Image.new('L', (64, 64), 0); ImageDraw.Draw(im).text((8, 8), '가', font=font, fill=255)
        _ttf[path] = (font, im.point(lambda v: 255 if v >= thr else 0).getbbox()[1])
    font, top = _ttf[path]
    im = Image.new('L', (64, 64), 0); ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=255)
    im = im.point(lambda v: 255 if v >= thr else 0)
    bb = im.getbbox()
    if not bb: return set()
    px = im.load()
    return {(x - bb[0], y - top) for x in range(bb[0], bb[2]) for y in range(bb[1], bb[3]) if px[x, y]}


def ink_of(ch, spec):
    """글자 잉크 화소 집합(칸 좌표, 왼쪽 위 = 0,0) — 한글 잉크 맨 위가 0 이 되게 맞춤"""
    if spec.get('ttf') and ch != '…':
        return ttf_ink(ch, spec)
    f = bdf(spec['bdf'])
    if ch == '…':  # 한국식 말줄임표: 바닥선 점 셋 한 칸
        ref, _ = f.draw('가')
        base = max(y for _, y in ref)
        top = min(y for _, y in ref)
        pts = [(1 + 4 * i, base - top) for i in range(3)]
        if spec['bdf'].endswith('Bold'):
            pts += [(x + 1, y) for x, y in pts]
    else:
        pts, _ = f.draw(ch)
        ref, _ = f.draw('가')
        top = min(y for _, y in ref)
        pts = [(x, y - top) for x, y in pts]
    s = spec['scale']
    out = set()
    for x, y in pts:
        for dx in range(s):
            for dy in range(s):
                out.add((x * s + dx, y * s + dy))
    return out


def render(ch, spec):
    """→ RGBA 그림(칸 크기)"""
    cw, chh, o = spec['cw'], spec['ch'], spec['outline']
    ink = ink_of(ch, spec)
    ink = {(x + o, y + o) for x, y in ink}
    im = Image.new('RGBA', (cw, chh), (0, 0, 0, 0))
    px = im.load()
    if spec['fmt'] == FMT_IA8:
        for x, y in ink:
            if 0 <= x < cw and 0 <= y < chh:
                px[x, y] = (255, 255, 255, 255)
        return im
    hmax = max((y for _, y in ink), default=0)
    hmin = min((y for _, y in ink), default=0)
    cols = grad(spec['grad'], hmax - hmin + 1)
    edge = set()
    for x, y in ink:
        for dx in range(-o, o + 1):
            for dy in range(-o, o + 1):
                edge.add((x + dx, y + dy))
    if spec.get('shadow'):
        sc = spec['shadow'] if isinstance(spec['shadow'], tuple) else (0, 0, 0)
        for x, y in list(edge):
            p = (x + 1, y + 1)
            if 0 <= p[0] < cw and 0 <= p[1] < chh:
                px[p] = sc + (255,)
    ecols = grad(spec['edge_grad'], hmax - hmin + 1 + 2 * o) if spec.get('edge_grad') else None
    for x, y in edge:
        if 0 <= x < cw and 0 <= y < chh:
            px[x, y] = (ecols[min(max(y - hmin + o, 0), len(ecols) - 1)] if ecols else spec['edge']) + (255,)
    for x, y in ink:
        if 0 <= x < cw and 0 <= y < chh:
            px[x, y] = cols[y - hmin] + (255,)
    return im


def encode(im, fmt):
    w, h = im.size
    px = im.load()
    rows = []
    for y in range(h):
        b = bytearray()
        for x in range(w):
            r, g, bl, a = px[x, y]
            if fmt == FMT_RGBA16:
                v = ((r >> 3) << 11) | ((g >> 3) << 6) | ((bl >> 3) << 1) | (1 if a >= 128 else 0)
                b += struct.pack('>H', v)
            else:  # IA8
                i = (r + g + bl) // 3 >> 4
                b.append((i << 4) | (a >> 4))
        # LoadTextureBlockS(dxt=0) — 홀수 줄은 8바이트 안에서 4바이트 맞바꿈
        if y & 1:
            assert len(b) % 8 == 0
            for k in range(0, len(b), 8):
                b[k:k + 8] = b[k + 4:k + 8] + b[k:k + 4]
        rows.append(bytes(b))
    return b''.join(rows)


def build(charset, outdir, prevdir):
    os.makedirs(outdir, exist_ok=True)
    table = b''
    data = b''
    for fid in range(4):
        sp = SPECS[fid]
        imgsz = sp['cw'] * sp['ch'] * 2 if sp['fmt'] == FMT_RGBA16 else sp['cw'] * sp['ch']
        bpc = 16 + imgsz
        bpc = (bpc + 7) & ~7
        table += struct.pack('>BBBBBBBBii', 0, sp['cw'], sp['ch'], sp['adv'], sp['yoff'] & 0xFF, 0, 0, 0, len(data), bpc)
        for ch in charset:
            im = render(ch, sp)
            g = struct.pack('>iiBBBBBBBB', 16, -1, sp['fmt'], 0, 0, 0, sp['cw'], sp['ch'], sp['adv'], 0)
            g += encode(im, sp['fmt'])
            g += b'\0' * (bpc - len(g))
            data += g
        data += b'\0' * ((-len(data)) % 16)
    open(os.path.join(outdir, 'kr_font.bin'), 'wb').write(data)
    open(os.path.join(outdir, 'kr_font_table.bin'), 'wb').write(table)
    if prevdir:
        preview(charset, prevdir)
    return len(data)


def preview(charset, prevdir):
    """글자판(원본 영문 | 한글) — 4배 확대, 게임 바탕색 비슷한 남색 바탕"""
    os.makedirs(prevdir, exist_ok=True)
    look = os.path.join(ROOT, 'work/us/fontlook')
    eng = {0: ['funfont/funfont_0.png', 'funfont/funfont_1.png'], 1: ['smallfont/smallfont_1.png'],
           2: ['bigfont/bigfont_a.png', 'bigfont/bigfont_b.png', 'bigfont/bigfont_c.png'], 3: ['subtitlefont/subtitlefont_0.png']}
    names = {0: 'FunFont', 1: 'SmallFont', 2: 'BigFont', 3: 'SubtitleFont'}
    sample = [c for c in '디디콩레이싱모험시작옵션…' if c in charset] + charset[:40]
    for fid in range(4):
        sp = SPECS[fid]
        per = 20
        rows = (len(sample) + per - 1) // per
        W = max(per * sp['adv'] + 8, 300)
        engims = [Image.open(os.path.join(look, f)).convert('RGBA') for f in eng[fid]]
        eh = max(i.size[1] for i in engims)
        H = eh + 8 + rows * (sp['ch'] + 4) + 8
        out = Image.new('RGBA', (W, H), (40, 50, 110, 255))
        x = 4
        for i in engims:
            out.alpha_composite(i, (x, 4))
            x += i.size[0] + 4
        y0 = eh + 12
        for k, ch in enumerate(sample):
            im = render(ch, sp)
            out.alpha_composite(im, (4 + (k % per) * sp['adv'], y0 + (k // per) * (sp['ch'] + 4)))
        out = out.resize((W * 4, H * 4), Image.NEAREST)
        out.save(os.path.join(prevdir, '%d_%s_원본위_한글아래.png' % (fid, names[fid])))


if __name__ == '__main__':
    cs = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'work/kr/charset.txt'), encoding='utf-8') if l.strip('\n')]
    n = build(cs, os.path.join(ROOT, 'work/kr'), sys.argv[1] if len(sys.argv) > 1 else None)
    print('chars', len(cs), 'font bytes', n)
