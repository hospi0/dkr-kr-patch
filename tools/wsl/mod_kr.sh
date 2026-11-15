#!/bin/bash
# 한글 모드 생성·빌드 (WSL root): mod/kr 만들기 → build.py(reference-us-v80) → mod/out/dkr_korean.nrm
set -eo pipefail
P=/mnt/c/claude/project/dkr-kr-patch
python3 $P/tools/wsl/mkmod.py
bash $P/tools/wsl/mod_build.sh kr
mkdir -p $P/mod/out
cp /root/modwork/kr-out/dkr_korean.nrm $P/mod/out/
ls -la $P/mod/out/dkr_korean.nrm
