# src/panel_src.html -> gzip -> src/panel.h (PANEL_GZ dizisi)
import gzip, os
d=os.path.join(os.path.dirname(__file__),'../src/')
z=gzip.compress(open(d+'panel_src.html','rb').read(),9)
open(d+'panel.h','w').write('// src/panel_src.html dosyasından gzip ile üretildi (tools/panel_uret.py)\n#pragma once\n#include <pgmspace.h>\nconst uint8_t PANEL_GZ[] PROGMEM = {'+','.join(map(str,z))+'};\nconst size_t PANEL_GZ_LEN = %d;\n'%len(z))
print('ok',len(z))
