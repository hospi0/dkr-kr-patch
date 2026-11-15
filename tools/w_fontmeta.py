import json,os
os.chdir('/root/dkr/assets/.vanilla/us.v80/fonts')
for n in ['FunFont','SmallFont','BigFont','SubtitleFont']:
    d=json.load(open('game_fonts/%s.meta.json'%n))
    print(n,{k:v for k,v in d.items() if not isinstance(v,(list,dict))}, list(d.keys()))
    for k,v in d.items():
        if isinstance(v,(list,dict)): print('  ',k,str(v)[:300])
for i in range(4):
    d=json.load(open('jp_fonts/jp_font_%d.meta.json'%i))
    print('JP',i,{k:v for k,v in d.items() if not isinstance(v,(list,dict))})
    for k,v in d.items():
        if isinstance(v,(list,dict)): print('  ',k,str(v)[:300])
