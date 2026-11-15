#!/bin/bash
# DKR-R 고정 N64Recomp(81213c1) + DKR-R 패치 3개 → RecompModTool (모드 빌드용)
set -eo pipefail
cd /root/n64recomp
git checkout -q -- .
for p in /mnt/c/claude/project/dkr-kr-patch/ref/dkr-r/patches/n64recomp/*.patch; do
  git apply "$p"; echo "applied $(basename "$p")"
done
cmake --build build --target RecompModTool 2>&1 | tail -1
ls -la build/RecompModTool
