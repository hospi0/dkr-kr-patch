# 폭 검사용 자료: 영문 글꼴 글자 폭 + 대사 파일별 상자 폭
import json, os
V = '/root/dkr_orig/assets/.vanilla/us.v80/'
OUT = '/mnt/c/claude/project/dkr-kr-patch/work/'
meta = {}
for n in ['FunFont', 'SmallFont', 'BigFont', 'SubtitleFont']:
    d = json.load(open(V + 'fonts/game_fonts/%s.meta.json' % n))
    meta[n] = {'special': d['special-character-width'], 'chars': d['characters']}
json.dump(meta, open(OUT + 'us/font_meta.json', 'w'), ensure_ascii=False)
box = {}
TB = V + 'text/game/unknown/'
for i in range(85):
    for c in ('asset_game_text_%d.json' % i, 'asset_game_text_%d_v79.json' % i):
        if os.path.exists(TB + c):
            d = json.load(open(TB + c))
            for p in d.get('pages', []):
                for cmd in p:
                    if cmd['command'] == 'SetBorder':
                        v = cmd['value']
                        box[str(i)] = v['right'] + 65 - v['left']
json.dump(box, open(OUT + 'kr/tb_boxes.json', 'w'))
print('ok', len(box))
