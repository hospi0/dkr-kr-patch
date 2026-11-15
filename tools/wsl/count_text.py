import json, glob, os, collections
B = '/root/dkr/assets/.vanilla/us.v80/text/'
menu = json.load(open(B + 'menu/english_menu_text_v79.json'))['sections']
mb = sum(len(v.encode()) for v in menu.values() if isinstance(v, str))
print('menu entries', len(menu), 'bytes', mb, 'types', collections.Counter(type(v).__name__ for v in menu.values()))
tot = collections.Counter(); cnt = collections.Counter(); cmds = collections.Counter()
samples = {}
for f in sorted(glob.glob(B + 'game/unknown/*.json')):
    d = json.load(open(f))
    tt = d.get('text-type', 'raw' if 'raw' in d else '?')
    n = 0
    def walk(x):
        global n
        if isinstance(x, dict):
            if x.get('command') == 'Text' or x.get('command') == 'text':
                v = x.get('value', '')
                tot[tt] += len(v.encode()); cnt[tt] += 1
            if 'command' in x:
                cmds[x['command']] += 1
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    samples.setdefault(tt, os.path.basename(f))
print('game text bytes', dict(tot), 'lines', dict(cnt))
print('types sample', samples)
print('cmds', cmds.most_common())
