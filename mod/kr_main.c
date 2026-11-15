/* DKR-R 한글 모드 — SDK 쪽 (tools/wsl/mkmod.py 가 mod/kr/main.c 로 복사)
 * · asset_load / asset_table_load 뒤: 한글판에서 바뀐 에셋(대사 6·7, 메뉴 8·9, 코스 이름 24·25)을 한글 자원으로 덮어씀
 *   (표 에셋은 크기 같음, 글 에셋은 원본보다 작음 — mkmod.py 가 검사)
 * · load_fonts 뒤: 한글 글자 캐시 준비(kr_font.c) · 매 프레임 캐시 나이 줄임
 * · 타이틀 연출 캐릭터 이름 10개 포인터를 한글 문자열로 */
#include <dkr/magic_codes.h>

typedef unsigned int u32;
void kr_font_init(void);
void kr_font_tick(void);
#define gTitleCinematicText ((unsigned char *)0x800DFDBCu) /* reference-us-v80/symbols.ld (us.v80 고정 주소) */

static const char *const kAssetRes[64] = {
    [6] = "a6", [7] = "a7", [8] = "a8", [9] = "a9", [24] = "a24", [25] = "a25",
};
static DkrU32 kAssetSize[64];
static unsigned char *gScratch;
static DkrU32 sLoadIdx, sLoadAddr, sLoadOff, sLoadSize, sTableIdx;
static int sTitleDone;

static unsigned char *scratch(void) {
    if (!gScratch)
        gScratch = (unsigned char *)dkr_alloc(4096);
    return gScratch;
}

/* 자원 name[off, off+bytes) → 게임 메모리 dst (4 KB 씩, 자원 끝에서 자름) */
static void copy_res(const char *name, DkrU32 total, DkrU32 off, unsigned char *dst, DkrU32 bytes) {
    unsigned char *buf = scratch();
    if (!buf || off >= total)
        return;
    if (bytes > total - off)
        bytes = total - off;
    while (bytes) {
        DkrU32 n = bytes > 4096 ? 4096 : bytes, i;
        if (dkr_resource_read(name, off, buf, n) != n)
            return;
        for (i = 0; i < n; i++)
            dst[i] = buf[i];
        dst += n;
        off += n;
        bytes -= n;
    }
}

static DkrU32 res_size(DkrU32 idx) {
    if (idx >= 64 || !kAssetRes[idx])
        return 0;
    if (!kAssetSize[idx])
        kAssetSize[idx] = dkr_resource_size(kAssetRes[idx]);
    return kAssetSize[idx];
}

DKR_CALLBACK(before_asset_load) void kr_before_asset_load(void) {
    DkrGameCall c;
    dkr_game_context_read(&c);
    sLoadIdx = (DkrU32)c.r[4];
    sLoadAddr = (DkrU32)c.r[5];
    sLoadOff = (DkrU32)c.r[6];
    sLoadSize = (DkrU32)c.r[7];
}

/* ★글자 캐시(그림·표시 목록)는 RDRAM 8 MB 안이어야 렌더러가 읽음 — 모드 힙(0x81000000~)은 안 됨(화면 멈춤).
 *  부팅 때 게임이 코스 이름 표(24)의 «끝값 − 첫값» 만큼 이름 버퍼를 잡으므로, 한글 표로 덮을 때 끝값을 KR_EXTRA 만큼 늘려
 *  이름 버퍼(게임 메모리, 게임 끝까지 유지) 뒤쪽을 글자 캐시로 쓴다. */
#define KR_EXTRA 0xE000U
static u32 sNamesKr, sRegion, sRegionLeft;
static int sNamesBumped;

DKR_CALLBACK(after_asset_load) void kr_after_asset_load(void) {
    DkrU32 total = res_size(sLoadIdx);
    if (total && sLoadSize && sLoadSize < 0x100000)
        copy_res(kAssetRes[sLoadIdx], total, sLoadOff, (unsigned char *)sLoadAddr, sLoadSize);
    if (sLoadIdx == 25 && sNamesBumped == 1 && sLoadOff == 0 && sLoadSize == sNamesKr + KR_EXTRA) {
        u32 a = (sLoadAddr + sNamesKr + 15) & ~15U;
        sRegion = a;
        sRegionLeft = sLoadAddr + sLoadSize - a;
        sNamesBumped = 2;
    }
}

DKR_CALLBACK(before_asset_table_load) void kr_before_asset_table_load(void) {
    DkrGameCall c;
    dkr_game_context_read(&c);
    sTableIdx = (DkrU32)c.r[4];
}

DKR_CALLBACK(after_asset_table_load) void kr_after_asset_table_load(void) {
    DkrGameCall c;
    DkrU32 total = res_size(sTableIdx), out;
    if (!total)
        return;
    dkr_game_context_read(&c);
    out = (DkrU32)c.r[2];
    if (!out)
        return;
    copy_res(kAssetRes[sTableIdx], total, 0, (unsigned char *)out, total);
    if (sTableIdx == 24 && !sNamesBumped) {
        int *t = (int *)out, i = 0;
        while (i < 256 && t[i] != -1)
            i++;
        if (i >= 2 && i < 256) {
            sNamesKr = (u32)(t[i - 1] - t[0]);
            t[i - 1] += (int)KR_EXTRA;
            sNamesBumped = 1;
        }
    }
}

/* ---- 한글 글꼴: kr_font.c 에서 부름 ---- */
/* 글자 캐시용 = 게임 메모리 구역에서 차례로(16 B 정렬) */
void *kr_alloc(u32 bytes) {
    u32 a, n = (bytes + 15) & ~15U;
    if (!sRegion || n > sRegionLeft)
        return (void *)0;
    a = sRegion;
    sRegion += n;
    sRegionLeft -= n;
    for (u32 i = 0; i < bytes; i++)
        ((unsigned char *)a)[i] = 0;
    return (void *)a;
}

/* 모드 힙(CPU 만 읽는 것) */
static void *mod_alloc(u32 bytes) {
    unsigned char *p = (unsigned char *)dkr_alloc(bytes + 16);
    return p ? (void *)(((u32)p + 15) & ~15U) : (void *)0;
}

void *kr_load_table(void) {
    void *t = mod_alloc(64);
    if (t)
        dkr_resource_read("a45", 0, t, 64);
    return t;
}

void kr_read_font(void *dst, int offset, int bytes) {
    dkr_resource_read("a46", (DkrU32)offset, dst, (DkrU32)bytes);
}

/* 타이틀 연출 이름(menu.c gTitleCinematicText[10], 44 B 레코드 첫 칸 = char*) */
static void kr_title_names(void) {
    DkrU32 size = dkr_resource_size("title"), i, k = 0;
    char *s;
    unsigned char *rec = gTitleCinematicText;
    if (sTitleDone || !size || !rec)
        return;
    s = (char *)mod_alloc(size);
    if (!s || dkr_resource_read("title", 0, s, size) != size)
        return;
    for (i = 0; i < 10 && k < size; i++) {
        *(char **)(rec + 44 * i) = s + k;
        while (k < size && s[k])
            k++;
        k++;
    }
    sTitleDone = 1;
}

/* ---- 글자 찍기·폭: 시작 훅에서 한글판 처리 후 원래 함수 건너뜀(바꿔치기는 DKR-R 이 보호 함수로 거부) ---- */
void kr_render_text_string(void *dList, void *box, char *text, int alignmentFlags, float scisScale);
int kr_get_text_width(char *text, int x, int font);

/* 게임 함수 호출용 모드 소유 스택(DKR-R: «Game call requires a mod-owned aligned guest stack») */
static unsigned char sCallStack[8192] __attribute__((aligned(16)));

void kr_call_dl(const char *name, void *dList) {
    DkrGameCall c;
    for (int i = 0; i < 32; i++)
        c.r[i] = 0, c.f[i] = 0;
    c.hi = c.lo = 0;
    c.fcsr = c.padding = 0;
    c.r[4] = (DkrU64)(long long)(int)(u32)dList;
    c.r[29] = (DkrU64)(long long)(int)(((u32)(sCallStack + sizeof(sCallStack)) - 64) & ~15U);
    dkr_game_call(name, &c);
}

static int sKrReady;

/* 글자 캐시 준비: 구역이 생긴 뒤 처음 쓸 때(약 52 KB 필요) */
static int kr_ready(void) {
    if (!sKrReady && sNamesBumped == 2 && sRegionLeft >= 0xD000U) {
        kr_font_init();
        sKrReady = 1;
    }
    return sKrReady;
}

DKR_CALLBACK(before_render_text_string) void kr_before_render_text_string(void) {
    DkrGameCall c;
    union { u32 w; float f; } s;
    if (!kr_ready())
        return;
    dkr_game_context_read(&c);
    /* O32: a0 dList, a1 box, a2 text, a3 정렬, 다섯째(f32) = 스택 sp+16 */
    char *text = (char *)(u32)c.r[6];
    s.w = *(volatile u32 *)((u32)c.r[29] + 16);
    if (!text)
        return;
    kr_render_text_string((void *)(u32)c.r[4], (void *)(u32)c.r[5], text, (int)c.r[7], s.f);
    /* 원래 함수는 건너뛸 수 없음(«Project-owned game fixes cannot be skipped») → 같은 글의 끝(빈 문자열)을 넘겨 아무것도 안 찍게.
       원래 함수는 box->xpos 를 읽고 그대로 되돌려 놓으므로 한글판이 옮긴 위치가 유지됨 */
    while (*text)
        text++;
    c.r[6] = (DkrU64)(long long)(int)(u32)text;
    dkr_game_context_write(&c);
}

static u32 sWidthText, sWidthX, sWidthFont;

DKR_CALLBACK(before_get_text_width) void kr_before_get_text_width(void) {
    DkrGameCall c;
    dkr_game_context_read(&c);
    sWidthText = (u32)c.r[4];
    sWidthX = (u32)c.r[5];
    sWidthFont = (u32)c.r[6];
}

DKR_CALLBACK(after_get_text_width) void kr_after_get_text_width(void) {
    DkrGameCall c;
    if (!sWidthText || !kr_ready())
        return;
    dkr_game_context_read(&c);
    c.r[2] = (DkrU64)(long long)kr_get_text_width((char *)sWidthText, (int)sWidthX, (int)sWidthFont);
    dkr_game_context_write(&c);
    sWidthText = 0;
}

DKR_CALLBACK(after_load_fonts) void kr_after_load_fonts(void) {
    kr_title_names();
}

DKR_CALLBACK(on_frame) void kr_frame(void) {
    if (sKrReady)
        kr_font_tick();
}
