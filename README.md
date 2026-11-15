# 디디콩 레이싱 (N64) 한글 패치

> **내려받기:** [릴리즈 페이지](https://github.com/hospi0/dkr-kr-patch/releases/latest) — v0.9.
> 북미판 **Diddy Kong Racing (USA) (En,Fr) (Rev 1)** 롬용 xdelta 패치입니다.
>
> 이 저장소에는 도구·번역 텍스트·작업 문서만 있습니다(게임 데이터·롬 없음).

## 적용

```
Diddy Kong Racing (USA) (En,Fr) (Rev 1) 에 패치하시면 됩니다.

원본md5 : B31F8CCA50F31ACC9B999ED5B779D6ED
패치md5 : 570A4117B2BC5412EFE9FDC7D2D892F6

입니다.
```

xdelta 적용기(Delta Patcher 등)로 원본 롬(z64)에 `DKR_KR_v0.9.xdelta` 를 적용합니다.

## 바뀌는 것

- 메뉴·옵션·대사 상자·자막·코스 이름 등 글자로 나오는 문장 전부(716줄)
- 한글 글꼴 4종: 메뉴 글꼴(영문판 색 그대로), 작은 글꼴, 큰 제목 글꼴(나눔고딕 ExtraBold), 자막 글꼴
- 그림으로 박힌 글자(타이틀 로고·일부 메뉴 제목 그림·HUD)는 아직 원문입니다. 엔딩 스태프 롤도 원문 그대로입니다.

## 만든 방법

[디컴파일 프로젝트](https://github.com/DavidSM64/Diddy-Kong-Racing)(us.v80)를 WSL 우분투에서 빌드하면서
영문 글자 출력에 2바이트 한글 경로를 넣었습니다(미국판에서 안 쓰는 일본어 글꼴 자리를 한글 글꼴로 재사용, 한 글자씩 읽어 캐시).

| 경로 | 내용 |
|---|---|
| `tools/prep_kr.py` | 번역 조판 검사·문자표·글꼴 만들기 |
| `tools/mkfont.py` | 한글 글꼴 4종(갈무리·나눔고딕) |
| `tools/wsl/build.sh` | 우분투에서 패치 적용 → 빌드 |
| `tools/wsl/patch_src.py`, `patch_tool.py`, `apply_kr.py` | 소스(font.c)·에셋 도구·번역 적용 |
| `work/kr/ko.tsv` | 번역 |
| `docs/00_초기조사.md` | 작업 기록 |

## 글꼴

- [갈무리](https://github.com/quiple/galmuri) — SIL Open Font License 1.1
- [나눔고딕](https://hangeul.naver.com/font) — SIL Open Font License 1.1
