# TTF -> VLW (Processing smooth font) -> C dizisi (PROGMEM). LovyanGFX loadFont(dizi) ile kullanılır.
import freetype, struct, os
G='/usr/share/fonts/truetype/sand-box/google/'
TR="ÇĞİÖŞÜçğıöşü"
ASCII=''.join(chr(c) for c in range(32,127))
FONTS=[ # ad, dosya, piksel, karakterler, varyasyon(wght)
 ('f_baslik',G+'Orbitron/Orbitron-VariableFont_wght.ttf',17,"LASTİK ŞİŞİRME",500),
 ('f_rakam', G+'Orbitron/Orbitron-VariableFont_wght.ttf',52,"0123456789.-",500),
 ('f_etiket',G+'Rajdhani/Rajdhani-Medium.ttf',13,ASCII+TR+"•",None),
 ('f_kucuk', G+'Rajdhani/Rajdhani-Medium.ttf',18,ASCII+TR,None),
 ('f_kalin', G+'Rajdhani/Rajdhani-Bold.ttf',24,ASCII+TR,None),
]
def vlw(path,px,chars,wght):
    f=freetype.Face(path)
    if wght:
        try: f.set_var_design_coords((wght,))
        except Exception: pass
    f.set_pixel_sizes(0,px)
    chars=sorted(set(chars)); gl=[]; bm=b''
    asc=f.size.ascender>>6; desc=-(f.size.descender>>6)
    for ch in chars:
        f.load_char(ch, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_LIGHT)
        g=f.glyph; b=g.bitmap; w,h=b.width,b.rows
        data=bytes(b.buffer[r*b.pitch+c] for r in range(h) for c in range(w))
        gl.append((ord(ch),h,w,(g.advance.x+32)>>6,g.bitmap_top,g.bitmap_left,0)); bm+=data
    out=struct.pack('>6i',len(gl),11,px,0,asc,desc)
    for x in gl: out+=struct.pack('>7i',*x)
    return out+bm
h=['// Otomatik üretildi: tools/vlw_uret.py\n#pragma once\n#include <pgmspace.h>\n']
for ad,p,px,ch,w in FONTS:
    d=vlw(p,px,ch,w)
    h.append(f'// {os.path.basename(p)} {px}px, {len(d)} bayt\nconst uint8_t {ad}[] PROGMEM = {{'+','.join(str(x) for x in d)+'};\n')
open(os.path.join(os.path.dirname(__file__),'../src/fontlar.h'),'w').write(''.join(h))
print('ok')
