# 게임 소스(~/dkr/src) 한글 패치 — 미국판 글자 출력에 2바이트 한글 경로를 붙인다.
# 한글 코드: 두 바이트 모두 0x80 이상, 색인 = ((b0&0x7F)<<7) | (b1&0x7F)
# 글꼴 자료 = ASSET_JAPANESE_FONTS(미국판에선 안 쓰는 자리)를 한글 글꼴로 교체,
# 머리표 = ASSET_JAPANESE_FONTS_TABLE (글꼴 4개 × 16 B)
import re, sys, subprocess
R = '/root/dkr/src/'
# 늘 원본에서 다시 시작
subprocess.check_call(['git', '-C', '/root/dkr', 'checkout', '--', 'src/font.c', 'src/font.h', 'src/thread3_main.c'])

def sub1(s, old, new, tag):
    if old not in s:
        print('NOT FOUND:', tag); sys.exit(1)
    return s.replace(old, new, 1)

p = R + 'font.c'
s = open(p).read()
if 'KR_FONT' not in s:
    # 1) 한글 캐시 코드(일본판 캐시를 옮겨 씀)
    s = sub1(s, 's8 sDialogueBoxCloseTimer;', r'''s8 sDialogueBoxCloseTimer;

#if REGION != REGION_JP
/* ===== KR_FONT : 한글 글자 캐시 ===== */
typedef struct KrFontHeader {
    u8 unk0;
    u8 x;          // 칸 폭
    u8 y;          // 칸 높이
    u8 charWidth;  // 한글 한 글자 전진 폭
    s8 yOffset;    // 줄 위에서 내려 찍는 양(음수 가능)
    u8 pad[3];
    s32 offsetToData;
    s32 bytesPerCharacter;
} KrFontHeader;

typedef struct KrGlyph {
    s32 img;  // 그림 오프셋(머리 기준)
    s32 img2; // -1
    u8 fmt;   // Asset46.unk8 : 1 RGBA16, 5 IA8
    u8 fmt2;
    u8 left, top, right, bottom;
    u8 spacing;
    u8 pad;
} KrGlyph;

typedef struct KrSlot {
    u8 age;
    u8 units;
    u16 key;
    Gfx *dList;
} KrSlot;

#define KR_UNITS 128
#define KR_UNIT_SIZE 0x120

KrFontHeader *gKrFontHeaders = NULL;
KrSlot *gKrSlots = NULL;
u8 *gKrData = NULL;
Gfx *gKrDLists = NULL;

void fontCreateDisplayList(Gfx *dList, Asset46 *asset, s32 width, s32 height);

void kr_font_init(void) {
    s32 i, g;
    gKrDLists = mempool_alloc_safe(KR_UNITS * 14 * sizeof(Gfx), COLOUR_TAG_RED);
    gKrSlots = mempool_alloc_safe(KR_UNITS * sizeof(KrSlot), COLOUR_TAG_RED);
    gKrData = mempool_alloc_safe(KR_UNITS * KR_UNIT_SIZE, COLOUR_TAG_RED);
    for (i = 0, g = 0; i < KR_UNITS; i++) {
        gKrSlots[i].age = 0;
        gKrSlots[i].units = 0;
        gKrSlots[i].key = 0xFFFF;
        gKrSlots[i].dList = &gKrDLists[g];
        g += 14;
    }
    gKrFontHeaders = (KrFontHeader *) asset_table_load(ASSET_JAPANESE_FONTS_TABLE);
}

/* 매 프레임: 쓴 지 2프레임 지난 칸을 비운다 */
void kr_font_tick(void) {
    s32 i;
    if (gKrSlots == NULL) {
        return;
    }
    for (i = 0; i < KR_UNITS; i++) {
        if (gKrSlots[i].age) {
            gKrSlots[i].age--;
        }
    }
}

s32 kr_font_advance(s32 font) {
    if (gKrFontHeaders == NULL || font < 0 || font > 3) {
        return 12;
    }
    return gKrFontHeaders[font].charWidth;
}

static s32 kr_cache_get(s32 font, u16 code) {
    s32 i, j, need, found;
    u16 key;
    KrFontHeader *h = &gKrFontHeaders[font];
    KrGlyph *glyph;

    key = (font << 12) | (code & 0xFFF);
    need = (h->bytesPerCharacter + KR_UNIT_SIZE - 1) / KR_UNIT_SIZE;
    for (i = 0; i + need <= KR_UNITS; i += need) {
        if (gKrSlots[i].age != 0 && gKrSlots[i].key == key) {
            return i;
        }
    }
    found = -1;
    for (i = 0; i + need <= KR_UNITS && found < 0; i += need) {
        found = i;
        for (j = 0; j < need; j++) {
            if (gKrSlots[i + j].age != 0) {
                found = -1;
                break;
            }
        }
    }
    if (found < 0) {
        return -1;
    }
    for (j = 0; j < need; j++) {
        gKrSlots[found + j].units = need;
        gKrSlots[found + j].key = (j == 0) ? key : 0xFFFF;
    }
    glyph = (KrGlyph *) &gKrData[found * KR_UNIT_SIZE];
    asset_load(ASSET_JAPANESE_FONTS, (u32) glyph, h->offsetToData + (h->bytesPerCharacter * code),
               h->bytesPerCharacter);
    fontCreateDisplayList(gKrSlots[found].dList, (Asset46 *) glyph, h->x, h->y);
    return found;
}

/* 한 글자 찍기. 돌려주는 값 = 전진 폭 */
s32 kr_draw_glyph(Gfx **dList, DialogueBoxBackground *box, s32 font, u16 code, s32 xpos, s32 ypos) {
    KrFontHeader *h;
    s32 idx, j, ulx, uly, lrx, lry, s, t;

    if (gKrFontHeaders == NULL || font < 0 || font > 3) {
        return 0;
    }
    h = &gKrFontHeaders[font];
    ulx = box->x1 + xpos;
    uly = box->y1 + ypos + h->yOffset;
    lrx = ulx + h->x;
    lry = uly + h->y;
    if (lrx <= 0 || lry <= 0 || ulx >= box->x2 + 1 || uly >= box->y2 + 1) {
        return h->charWidth;
    }
    idx = kr_cache_get(font, code);
    if (idx < 0) {
        return h->charWidth;
    }
    for (j = 0; j < gKrSlots[idx].units; j++) {
        gKrSlots[idx + j].age = 2;
    }
    gSPDisplayList((*dList)++, gKrSlots[idx].dList);
    s = 0;
    t = 0;
    if (ulx < 0) {
        s = -ulx;
        ulx = 0;
    }
    if (uly < 0) {
        t = -uly;
        uly = 0;
    }
    gSPTextureRectangle((*dList)++, ulx << 2, uly << 2, lrx << 2, lry << 2, 0, s << 5, t << 5, 1 << 10, 1 << 10);
    return h->charWidth;
}
#endif
''', 'kr block')

    # 2) load_fonts 에서 한글 초기화
    s = sub1(s, '''    load_font(ASSET_FONTS_FUNFONT);
    load_font(ASSET_FONTS_SMALLFONT);
#endif''', '''    load_font(ASSET_FONTS_FUNFONT);
    load_font(ASSET_FONTS_SMALLFONT);
    kr_font_init();
#endif''', 'load_fonts')

    # 3) render_text_string(미국판): 0x80 이상 두 바이트 = 한글
    s = sub1(s, '''            curChar = text[charIndex];
            newData = FALSE;
            charSpace = 0;
            if (curChar <= 0x20 || curChar >= 0x80) {''', '''            curChar = text[charIndex];
            newData = FALSE;
            charSpace = 0;
            if (curChar >= 0x80 && ((u8) text[charIndex + 1] & 0x80)) {
                charSpace = kr_draw_glyph(dList, box, box->font,
                                          ((curChar & 0x7F) << 7) | ((u8) text[charIndex + 1] & 0x7F), xpos, ypos);
                charIndex++;
                lastTextureIndex = -1;
                gDkrDmaDisplayList((*dList)++, OS_K0_TO_PHYSICAL(dDialogueBoxDrawModes[0]), 2);
            } else if (curChar <= 0x20 || curChar >= 0x80) {''', 'render')

    # 4) get_text_width(미국판)
    s = sub1(s, '''        thisDiffX = diffX;
        ch = text[index];
        if (ch <= 0x20 || ch >= 0x80) {''', '''        thisDiffX = diffX;
        ch = text[index];
        if (ch >= 0x80 && ((u8) text[index + 1] & 0x80)) {
            diffX += kr_font_advance(font);
            index++;
        } else if (ch <= 0x20 || ch >= 0x80) {''', 'width')

    # 5) fontCreateDisplayList 를 미국판에서도 쓰도록: 일본판 전용 블록 밖으로 복사
    m = re.search(r'/\*\*\n \* Official Name: fontCreateDisplayList\n \*/\nvoid fontCreateDisplayList.*?\n}\n', s, re.S)
    fcd = m.group(0)
    s = s.rstrip('\n')
    assert s.endswith('#endif')
    s += '\n\n#if REGION != REGION_JP\n' + fcd + '#endif\n'
    open(p, 'w').write(s)
    print('font.c ok')

p = R + 'thread3_main.c'
s = open(p).read()
if 'kr_font_tick' not in s:
    s = sub1(s, '''#if REGION == REGION_JP
    func_800C78E0_C84E0();
#endif
}''', '''#if REGION == REGION_JP
    func_800C78E0_C84E0();
#else
    kr_font_tick();
#endif
}''', 'tick')
    s = sub1(s, '#include', 'void kr_font_tick(void);\n#include', 'proto') if False else s
    open(p, 'w').write(s)
    print('thread3 ok')

p = R + 'font.h'
s = open(p).read()
if 'kr_font_tick' not in s:
    s = s.replace('void load_fonts(void);', 'void load_fonts(void);\nvoid kr_font_tick(void);\nvoid kr_font_init(void);', 1)
    open(p, 'w').write(s)
    print('font.h ok')
