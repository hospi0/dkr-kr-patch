# -*- coding: utf-8 -*-
"""번역(work/kr/ko.tsv) → 조판 규칙 적용 · 문자표 · 글꼴 · 폭 검사

출력: work/kr/ko_norm.json  {id: 한글(규칙 적용)}
      work/kr/charset.txt   (한 줄 한 글자, 색인 = 게임 코드)
      work/kr/kr_font.bin / kr_font_table.bin (mkfont)
폭이 넘치면 멈춘다(쓰는 순간 막기).
"""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import mkfont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
KR = os.path.join(ROOT, 'work/kr')

# 표준 문장부호(이 게임의 ~ 는 숫자 자리 표시라 뺌)
PUNCT = ",.!?:;)]}'\"、。，．！？：；）］｝」』】〉》”’…‥・·～〜♪♥"


def squeeze(t):
    t = re.sub(r'\.{3,}|…{2,}|‥+', '…', t)
    return re.sub('([' + re.escape(PUNCT) + '])[ 　](?![ 　])', r'\1', t)


# 영문 글꼴 글자 폭(get_text_width 와 같은 계산) — 원본 메타에서
FONT_META = os.path.join(ROOT, 'work/us/font_meta.json')


def load_meta():
    return json.load(open(FONT_META, encoding='utf-8'))


def text_width(s, font, meta):
    m = meta[font]
    w = 0
    adv = mkfont.SPECS[{'FunFont': 0, 'SmallFont': 1, 'BigFont': 2, 'SubtitleFont': 3}[font]]['adv']
    for ch in s:
        if ord(ch) >= 0x80:
            w += adv
        elif ch == ' ' or ord(ch) < 0x20:
            w += m['special']
        else:
            c = m['chars'].get(ch)
            if c and c.get('tex-index', -1) != -1:
                w += c['char-width']
            else:
                w += m['special']
    return w


def main():
    src = {}
    for ln in open(os.path.join(KR, 'en_source.tsv'), encoding='utf-8'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3:
            src[p[0]] = p
    ko = {}
    for n, ln in enumerate(open(os.path.join(KR, 'ko.tsv'), encoding='utf-8'), 1):
        ln = ln.rstrip('\n')
        if not ln:
            continue
        k, v = ln.split('\t', 1)
        if k in ko:
            sys.exit('중복 id %s (줄 %d)' % (k, n))
        ko[k] = squeeze(v.replace('{sp}', ' '))
    miss = [k for k in src if k not in ko]
    if miss:
        sys.exit('번역 빠짐 %d: %s' % (len(miss), miss[:10]))
    errs = []
    for k, v in ko.items():
        if k in src:
            en = src[k][2]
            if en.count('~') != v.count('~'):
                errs.append('~ 개수 다름 %s [%s] [%s]' % (k, en, v))
        if '\\n' in v or '\t' in v:
            errs.append('줄바꿈/탭 %s' % k)
    # 폭 검사
    meta = load_meta()
    box = json.load(open(os.path.join(KR, 'tb_boxes.json'), encoding='utf-8'))
    for k, v in ko.items():
        if k.startswith('tb:'):
            f = k.split(':')[1]
            bw = box.get(f, 170)
            fnt = 'FunFont'
            w = text_width(v, fnt, meta)
            if w > bw - 6:
                errs.append('상자 폭 넘침 %s 폭 %d > %d [%s]' % (k, w, bw - 6, v))
        elif k.startswith('dlg:'):
            w = text_width(v, 'SmallFont', meta)
            if w > 256 - 16:
                errs.append('자막 폭 넘침 %s %d [%s]' % (k, w, v))
    chars = sorted({c for v in ko.values() for c in v if ord(c) >= 0x80})
    # 글꼴에 없는 글자
    for c in chars:
        if c != '…' and ord(c) not in mkfont.bdf('Galmuri9').g:
            errs.append('갈무리9 에 없는 글자 %s' % c)
    if errs:
        print('\n'.join(errs))
        sys.exit('검사 실패 %d건' % len(errs))
    if len(chars) >= 0x3FFF:
        sys.exit('글자 너무 많음')
    open(os.path.join(KR, 'charset.txt'), 'w', encoding='utf-8').write('\n'.join(chars) + '\n')
    json.dump(ko, open(os.path.join(KR, 'ko_norm.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    n = mkfont.build(chars, KR, sys.argv[1] if len(sys.argv) > 1 else None)
    print('번역 %d줄 · 글자 %d자 · 글꼴 %d B' % (len(ko), len(chars), n))


if __name__ == '__main__':
    main()
