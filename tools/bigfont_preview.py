# -*- coding: utf-8 -*-
r"""큰 글꼴(BigFont 2, 32×28 RGBA16 1비트 알파) 해상도 후보 미리보기 (2026-11-15 하스피 «큰 폰트 너무 저해상도»)
  지금 = 갈무리11 굵은꼴 ×2 (11px → 22px 계단). 후보 = 벡터 글꼴을 원래 크기(~22px)로 그려 문턱값 → 화소 두 배 촘촘.
  python tools/bigfont_preview.py → work/look/bigfont_hires_<n>/ 글자판(맨 위 영문 원본, 아래 후보별)"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mkfont

F = 'C:/claude/utils/font/'
CANDS = [  # (이름, 파일, 글꼴 크기 px, 문턱값)
    ('주아', F + 'jua/Jua-Regular.ttf', 27, 110),
    ('도현', F + 'dohyeon/DoHyeon-Regular.ttf', 28, 110),
    ('나눔고딕ExtraBold', F + 'nanum-gothic/NanumGothicExtraBold.ttf', 24, 110),
]
INK_H = 22   # 한글 «가» 잉크 높이 목표(지금 갈무리 ×2 와 같음)


def ttf_ink(path, size, thr):
    font = ImageFont.truetype(path, size)
    def ref_box():
        im = Image.new('L', (64, 64), 0); ImageDraw.Draw(im).text((8, 8), '가', font=font, fill=255)
        return im.point(lambda v: 255 if v >= thr else 0).getbbox()
    rb = ref_box()
    def ink(ch, spec):
        im = Image.new('L', (64, 64), 0); ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=255)
        im = im.point(lambda v: 255 if v >= thr else 0)
        bb = im.getbbox()
        if not bb: return set()
        px = im.load()
        return {(x - bb[0], y - rb[1]) for x in range(64) for y in range(64) if px[x, y]}
    return ink, rb[3] - rb[1]


def main():
    n = 1
    while os.path.exists(os.path.join(ROOT, 'work', 'look', 'bigfont_hires_%d' % n)): n += 1
    od = os.path.join(ROOT, 'work', 'look', 'bigfont_hires_%d' % n); os.makedirs(od)
    words = ['어드벤처', '트랙', '옵션', '레이스 시작', '디디콩 레이싱', '타임 트라이얼', '각오는 됐나?']
    sp = dict(mkfont.SPECS[2])
    eng = [Image.open(os.path.join(ROOT, 'work/us/fontlook/bigfont', f)).convert('RGBA') for f in ('bigfont_a.png',)]
    rows = [('영문 원본', eng[0])]
    def line(inkf):
        old = mkfont.ink_of
        if inkf: mkfont.ink_of = inkf
        try:
            ims = []
            for w in words:
                W = len(w) * sp['adv'] + 16; im = Image.new('RGBA', (W, sp['ch']), (0, 0, 0, 0)); x = 0
                for ch in w:
                    if ch != ' ': im.alpha_composite(mkfont.render(ch, sp), (x, 0))
                    x += sp['adv'] if ch != ' ' else sp['adv'] // 2
                ims.append(im.crop((0, 0, x + 8, sp['ch'])))
            return ims
        finally:
            mkfont.ink_of = old
    sets = [('지금(갈무리11B ×2)', line(None))]
    for name, path, size, thr in CANDS:
        f, h = ttf_ink(path, size, thr)
        sets.append(('%s %dpx(가 높이 %d)' % (name, size, h), line(lambda ch, s, f=f: f(ch, s))))
    W = 900; H = 4 + eng[0].size[1] + 8 + len(sets) * (2 * (sp['ch'] + 6) + 18)
    out = Image.new('RGBA', (W, H), (40, 50, 110, 255)); d = ImageDraw.Draw(out)
    lab = ImageFont.truetype(F + 'nanum-gothic/NanumGothicBold.ttf', 12)
    out.alpha_composite(eng[0], (4, 4)); y = 4 + eng[0].size[1] + 8
    for name, ims in sets:
        d.text((4, y), name, font=lab, fill=(255, 255, 255, 255)); y += 16
        x = 4; yy = y
        for im in ims:
            if x + im.size[0] > W - 4: x = 4; yy += sp['ch'] + 6
            out.alpha_composite(im, (x, yy)); x += im.size[0]
        y = yy + sp['ch'] + 8
    out = out.crop((0, 0, W, y + 4))
    out.save(os.path.join(od, '큰글꼴_실제크기.png'))
    out.resize((out.size[0] * 2, out.size[1] * 2), Image.NEAREST).save(os.path.join(od, '큰글꼴_2배.png'))
    print(od)


if __name__ == '__main__':
    main()
