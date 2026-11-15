#!/bin/bash
# 사용: mod_build.sh <mod 폴더 이름(C:\claude\project\dkr-kr-patch\mod\ 아래)>
set -eo pipefail
S=/mnt/c/claude/project/dkr-kr-patch/ref/dkr-r/modding
P=/mnt/c/claude/project/dkr-kr-patch/mod/$1
W=/root/modwork/$1
rm -rf "$W" "$W-out"; mkdir -p "$(dirname "$W")"; cp -r "$P" "$W"
cd "$(dirname "$W")"
# 바꿔치기 함수는 symbols.ld 에서 빼야 함(안 빼면 링커 스크립트가 함수 이름을 게임 주소로 덮어 바꿔치기가 사라짐)
KIT=/root/modwork/kit-v80; rm -rf "$KIT"; cp -r "$S/reference-us-v80" "$KIT"
REPL=$(cat "$W/replace.txt" 2>/dev/null || true)
for f in $REPL; do sed -i "/^$f = /d" "$KIT/symbols.ld"; echo "symbols.ld 에서 뺌: $f"; done
python3 - "$KIT" <<'PY'
import hashlib, json, sys, os
k = sys.argv[1]; r = json.load(open(os.path.join(k, 'receipt.json')))
r['files']['symbols.ld'] = hashlib.sha256(open(os.path.join(k, 'symbols.ld'), 'rb').read()).hexdigest()
json.dump(r, open(os.path.join(k, 'receipt.json'), 'w'), indent=2)
PY
python3 "$S/build.py" "$1" --output "$1-out" --mod-tool /root/n64recomp/build/RecompModTool --reference-kit "$KIT" 2>&1 | tail -15
ls -la "$1-out"/*.nrm
