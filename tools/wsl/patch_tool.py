# 에셋 도구(dkr_assets_tool) 한글 패치 — ~/dkr 에 적용(여러 번 돌려도 같은 결과)
import re
R='/root/dkr/tools/dkr_assets_tool_src/'
p=R+'text/dkrText.cpp'; s=open(p,encoding='utf-8-sig').read()
if 'KR_CHARSET' not in s:
    s=s.replace('#include <algorithm>',r'''#include <algorithm>
#include <fstream>
#include <cstdlib>
#include <unordered_map>
''',1)
    s=s.replace('static bool string_has_non_ascii',r'''// ---- 한글: DKR_KR_CHARSET(UTF-8, 한 줄에 한 글자) 색인 i -> 0x80|(i>>7), 0x80|(i&0x7F)
static std::unordered_map<std::string,int> *KR_CHARSET = nullptr;
static bool kr_loaded = false;
static void kr_load() {
    if (kr_loaded) return;
    kr_loaded = true;
    const char *path = std::getenv("DKR_KR_CHARSET");
    if (!path) return;
    std::ifstream f(path);
    if (!f) { fprintf(stderr, "KR charset open fail %s\n", path); exit(1); }
    KR_CHARSET = new std::unordered_map<std::string,int>();
    std::string line; int i = 0;
    while (std::getline(f, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        (*KR_CHARSET)[line] = i++;
    }
}

static bool string_has_non_ascii''',1)
    s=s.replace('''    std::string curChar;
    size_t offset = 0;
    while (offset < _text.length()) {''',r'''    std::string curChar;
    size_t offset = 0;
    kr_load();
    if (!forceDKRJP && KR_CHARSET != nullptr) {
        while (offset < _text.length()) {
            _get_next_utf8_char(curChar, offset);
            if (curChar.length() == 1 && (unsigned char)curChar[0] < 0x80) {
                bytes.push_back(curChar[0]);
                continue;
            }
            auto it = KR_CHARSET->find(curChar);
            if (it == KR_CHARSET->end()) {
                // 일본어 자리(화면에 안 나옴)는 원래 DKRJP 부호로
                int jp = DataHelper::vector_index_of(DKRJP_FONT_CHARACTERS, curChar);
                if (jp != -1) {
                    bytes.push_back(0x80 | ((jp >> 8) & 0xFF));
                    bytes.push_back(jp & 0xFF);
                    continue;
                }
                fprintf(stderr, "KR charset missing char [%s] in text [%s]\n", curChar.c_str(), _text.c_str());
                exit(1);
            }
            bytes.push_back(0x80 | ((it->second >> 7) & 0x7F));
            bytes.push_back(0x80 | (it->second & 0x7F));
        }
        return bytes;
    }
    while (offset < _text.length()) {''',1)
    open(p,'w',encoding='utf-8').write(s)
p=R+'builder/buildTypes/buildJpFonts.cpp'; s=open(p).read()
if 'raw-data' not in s:
    s=s.replace('''    size_t numberOfFonts = jsonFile.length_of_array("/fonts-order");
    
    std::vector<uint8_t> outJpFontTable(numberOfFonts * sizeof(JpFontHeader));''',r'''    if (jsonFile.has("/raw-data")) {
        // 한글: 미리 만든 글꼴 자료·머리표를 그대로 넣는다
        fs::path dir = jsonFile.get_filepath().parent_path();
        info.out = FileHelper::read_binary_file(dir / jsonFile.get_string("/raw-data"));
        std::vector<uint8_t> rawTable = FileHelper::read_binary_file(dir / jsonFile.get_string("/raw-table"));
        info.get_collection().add_deferred_build_info("ASSET_JAPANESE_FONTS_TABLE", "ASSET_JAPANESE_FONTS_TABLE", info.get_build_id(),
            info.get_section_build_id(), rawTable, info.get_dst_folder() / deferInfo.outputPath, info.get_info_context());
        return;
    }
    size_t numberOfFonts = jsonFile.length_of_array("/fonts-order");
    
    std::vector<uint8_t> outJpFontTable(numberOfFonts * sizeof(JpFontHeader));''',1)
    assert 'raw-data' in s
    open(p,'w').write(s)
print('ok')
