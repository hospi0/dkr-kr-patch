#!/bin/bash
# 디디콩 레이싱 한글판 빌드 (WSL 우분투 root 에서)
# 앞서 Windows 에서: python tools/prep_kr.py  (문자표·글꼴·검사)
set -eo pipefail
T=/mnt/c/claude/project/dkr-kr-patch/tools/wsl
W=/mnt/c/claude/project/dkr-kr-patch/work
cd /root/dkr
python3 $T/patch_tool.py
make -C tools dkr_assets_tool -j20 > /tmp/tool.log 2>&1 || { tail -20 /tmp/tool.log; exit 1; }
python3 $T/patch_src.py
python3 $T/apply_kr.py
export DKR_KR_CHARSET=$W/kr/charset.txt
# 에셋이 바뀌어도 링크가 옛 오브젝트를 쓰는 일 방지
rm -f build/assets/assets.bin.o build/assets/assets.lut.bin.o build/dkr.us.v80.elf build/dkr.us.v80.bin build/dkr.us.v80.z64
make -j20 REGION=us VERSION=v80 NON_MATCHING=1 CC_CHECK=true > /tmp/kr_build.log 2>&1 || { grep -i -B2 -A6 'error\|fail' /tmp/kr_build.log | head -60; exit 1; }
mkdir -p $W/build
cp build/dkr.us.v80.z64 $W/build/dkr_kr.z64
ls -la $W/build/dkr_kr.z64
md5sum $W/build/dkr_kr.z64
python3 -c "import sys;z=open('$W/build/dkr_kr.z64','rb').read();k=open('$W/kr/kr_font_table.bin','rb').read();assert z.find(k)>0,'롬에 한글 글꼴 없음';print('글꼴 확인 OK')"
