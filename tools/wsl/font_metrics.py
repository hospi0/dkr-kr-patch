import json
B = '/root/dkr/assets/.vanilla/us.v80/fonts/game_fonts/'
for n in ['FunFont', 'SmallFont', 'BigFont', 'SubtitleFont']:
    d = json.load(open(B + n + '.meta.json'))
    print('==', n, 'fixed', d['fixed-width'], 'y-off', d['y-offset'], 'special', d['special-character-width'], 'tab', d['tab-width'])
    for ch in ['A', 'g', 'a', '0', '.', ',', '?', ' ']:
        c = d['characters'].get(ch)
        print('  ', repr(ch), c)
