"""JP 글꼴 4개(구역 45 머리·46 자료) → work/look/jpfont_N.png (16×16 칸, 256자)"""
import sys, os
from PIL import Image
ROM = r'C:/claude/roms/n64/Diddy Kong Racing (Japan).z64'
d = open(ROM, 'rb').read(); H, D = 0xAB7C10, 0xAB7C50
OUT = os.path.join(os.path.dirname(__file__), '..', 'work', 'look'); os.makedirs(OUT, exist_ok=True)
def deint(b, w, bpp):
    rb = w * bpp // 8; out = bytearray(b)
    for y in range(1, len(b) // rb, 2):
        r = out[y*rb:(y+1)*rb]
        for i in range(0, rb - 7, 8): r[i:i+4], r[i+4:i+8] = r[i+4:i+8], r[i:i+4]
        out[y*rb:(y+1)*rb] = r
    return bytes(out)
def px(fmt, b, w, h, inter):
    bpp = {1: 16, 5: 8, 3: 4}[fmt]
    if inter: b = deint(b, w, bpp)
    im = Image.new('RGBA', (w, h))
    for y in range(h):
        for x in range(w):
            i = y*w + x
            if fmt == 1:
                v = int.from_bytes(b[i*2:i*2+2], 'big'); r, g, bl, a = (v >> 11 & 31) * 8, (v >> 6 & 31) * 8, (v >> 1 & 31) * 8, (v & 1) * 255
            elif fmt == 5:
                v = b[i]; r = g = bl = (v >> 4) * 17; a = (v & 15) * 17
            else:
                v = (b[i // 2] >> (4 if i % 2 == 0 else 0)) & 15; r = g = bl = v * 17; a = 255 if v else 0
            im.putpixel((x, y), (r, g, bl, a))
    return im
inter = len(sys.argv) > 1
for f in range(4):
    h = d[H+f*16:H+f*16+16]; cw, ch = h[1], h[2]; off = int.from_bytes(h[8:12], 'big'); bpc = int.from_bytes(h[12:16], 'big')
    sheet = Image.new('RGBA', (cw*16, ch*16), (60, 60, 120, 255))
    for c in range(256):
        p = D + off + c*bpc; o1 = int.from_bytes(d[p:p+4], 'big'); fmt = d[p+8]
        g = px(fmt, d[p+o1:p+bpc], cw, ch, inter)
        sheet.alpha_composite(g, ((c % 16) * cw, (c // 16) * ch))
    sheet = sheet.resize((cw*16*3, ch*16*3), Image.NEAREST)
    sheet.save(os.path.join(OUT, 'jpfont_%d%s.png' % (f, '_i' if inter else '')))
print('ok')
