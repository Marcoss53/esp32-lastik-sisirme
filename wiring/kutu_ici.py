# Kutu ici baglanti semasi (ustten gorunum) - kutu v8 olculeri (mm), kapak acik bakis
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = "DejaVu Sans"
R, O, K, B, G, P, Y = '#d62728', '#ff8c00', '#111111', '#1f6fd1', '#1a9e3a', '#8e24aa', '#f2c500'
IX, IY = 207, 246
LX0 = 275                       # kapak ic yuzu paneli baslangici
def mx(x): return IX - x        # kutu.py x -> gorunum (kapak acik, onden bakis)
def lx(x): return LX0 + x       # kapak ic yuzu (ters cevrilmis)

fig = plt.figure(figsize=(24, 20), dpi=100)
ax = fig.add_axes([0.01, 0.26, 0.98, 0.68])
ax.set_xlim(-45, 490); ax.set_ylim(272, -14); ax.set_aspect('equal'); ax.axis('off')
fig.text(0.5, 0.972, "Kutu İçi Bağlantı Şeması (üstten görünüm)", ha='center', fontsize=30, weight='bold')
fig.text(0.5, 0.952, "Kapak açık, kutuya önden bakış  ·  ölçüler kutu v8 ile birebir (mm)", ha='center', fontsize=15, color='#555')

def rect(x0, y0, x1, y1, fc, ec='k', lw=1.8, z=3, **kw):
    ax.add_patch(Rectangle((min(x0, x1), min(y0, y1)), abs(x1-x0), abs(y1-y0), fc=fc, ec=ec, lw=lw, zorder=z, **kw))
def txt(x, y, t, fs=11, c='k', w='normal', ha='center', va='center', bg=None, z=8, **kw):
    bb = dict(fc=bg, ec='none', pad=1.2, alpha=0.9) if bg else None
    ax.text(x, y, t, fontsize=fs, color=c, weight=w, ha=ha, va=va, bbox=bb, zorder=z, **kw)
def wire(pts, c, lw=3.2, z=5):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=c, lw=lw, solid_capstyle='round', solid_joinstyle='round', zorder=z)
    ax.plot(*pts[0], 'o', color=c, ms=5, zorder=z+1, mec='k', mew=0.6); ax.plot(*pts[-1], 'o', color=c, ms=5, zorder=z+1, mec='k', mew=0.6)

# ---- kutu
ax.add_patch(FancyBboxPatch((-2, -2), IX+4, IY+4, boxstyle="round,pad=0,rounding_size=12", fc='#f4f4f4', ec='#444', lw=4, zorder=1))
rect(mx(75), 0, mx(72), IY, '#b8b8b8', ec='#666', lw=1, z=2)           # ara duvar
txt(mx(73.5), 115, "ARA DUVAR", fs=9, c='#555', rotation=90, bg='#b8b8b8')
txt(mx(140), 8, "PNÖMATİK BÖLME", fs=15, c='#777', w='bold')
txt(mx(36), -8, "ELEKTRONİK BÖLME", fs=15, c='#777', w='bold')

# ---- elektronik parcalar (kutu.py konumlari)
rect(mx(33), 11, mx(5), 66, '#cfe3ff', lw=2)
txt(mx(19), 36, "ESP32\nDevKit", fs=13, w='bold')
rect(mx(69), 3, mx(39), 73, '#d8efc9', lw=2)
txt(mx(54), 12, "PERTİNAKS 1", fs=10, w='bold')
rect(mx(54)-5.1, 50.7, mx(54)+5.1, 55.3, '#333', z=4); txt(mx(54), 59, "TIP102", fs=9, w='bold')
rect(mx(65.5), 76, mx(48), 88.2, '#ffe2bf', lw=2); txt(mx(56.75), 82, "5V BUCK", fs=9, w='bold')
rect(mx(30), 81.25, mx(0), 92.75, '#9a9a9a', lw=2); rect(mx(45), 83.5, mx(30), 90.5, '#9a9a9a', lw=1.5)
txt(mx(17), 87, "DC JAK", fs=9, w='bold', c='w')
rect(mx(69), 122, mx(39), 162, '#eeeeee', ec='#999', lw=1.5, ls='--')
txt(mx(54), 142, "PERTİNAKS 2\n(boş, 2. valf\nyedeği)", fs=8.5, c='#888')
# DC fis (dis)
rect(IX+2, 82, IX+22, 92, '#555'); txt(IX+24, 76, "12V 2A adaptör", fs=10, w='bold', ha='left')

# ---- pnömatik hat (kutu.py: s -> x = 15 + s, hat y = 226)
HY = 226
def X(s): return mx(15 + s)
rect(X(-27), HY-5.25, X(0), HY+5.25, '#d9b34a', z=3)                    # giris barbi
rect(X(0), HY-12, X(48), HY+18, '#c9a227', lw=2, z=3)                    # valf govde
rect(X(24)-20.9, 174.2, X(24)+20.9, 212, '#2b2b2b', z=4)                 # bobin
txt(X(24), 186, "VALF\n2W-025-08\n12V", fs=10, w='bold', c='w')
rect(X(48), HY-7, X(60), HY+7, '#aaa', z=3)                              # hizli gecme
rect(X(60), HY-4, X(80-14), HY+4, '#3b7dd8', z=3)                        # PU hortum
rect(X(66), HY-6.5, X(94), HY+6.5, '#999', lw=1.5, z=3)                  # T
rect(X(80)-11, 86.4, X(80)+11, 212, '#222', z=4)                         # sensor yigini
rect(X(80)-11, 140, X(80)+11, 165, '#c9a227', z=5)
txt(X(80), 112, "BASINÇ\nSENSÖRÜ\n200 PSI", fs=8.5, w='bold', c='w', z=9)
rect(X(94), HY-4, X(118), HY+4, '#3b7dd8', z=3)
rect(X(118), HY-8.5, X(147.2), HY+8.5, '#c9a227', lw=1.5, z=3)           # adaptor
rect(X(147.2), HY-8, -40, HY+8, '#1f4fa0', z=2)                          # cikis hortumu
for xa, xb in ((IX+40, IX+12), (X(52), X(62)), (X(100), X(112)), (-8, -36)):
    ax.add_patch(FancyArrowPatch((xa, HY), (xb, HY), arrowstyle='-|>', mutation_scale=26, color='#00b4ff', lw=3, zorder=7))
ax.plot([X(-27), IX+40], [HY, HY], color='#d9b34a', lw=8, zorder=2)
txt(IX+26, HY+15, "HAVA GİRİŞİ\n(kompresör)", fs=11, w='bold', c='#0077b6')
txt(-22, HY+19, "ÇIKIŞ\n(lastiğe)", fs=11, w='bold', c='#0077b6')
for x_, t in ((X(24), "valf gövdesi"), (X(80), "hızlı geçme T"), (X(132), "adaptör")):
    txt(x_, HY+24, t, fs=9.5, c='#444')

# ---- kablolar (kutu ici)
# +12V
wire([(mx(30), 84), (mx(42), 84), (mx(46), 84)], R)                                 # jak -> buck IN (kisa)
wire([(mx(30)-0, 90), (mx(36), 90), (mx(36), 100), (mx(36), 174.2)], R)             # jak -> valf +
txt(mx(36)+1.5, 168, "+", fs=13, w='bold', c=R, ha='left')
txt(mx(36)+2, 118, "+12V", fs=10, c=R, w='bold', ha='left', rotation=90)
# GND
wire([(mx(30), 87), (mx(47), 87)], K)
wire([(mx(50), 76), (mx(50), 73)], K)                                                  # buck GND -> pert GND
wire([(mx(39), 58), (mx(33), 58)], K)                                                  # pert GND -> ESP GND
# 5V
wire([(mx(62), 76), (mx(62), 74.5), (mx(20), 74.5), (mx(20), 66)], O)                  # buck OUT -> VIN
wire([(mx(65.5), 80), (X(80)+5, 80), (X(80)+5, 86.4)], O)                              # buck OUT -> sensor kirmizi
# sensor sinyal + GND -> pertinaks
wire([(X(80), 86.4), (X(80), 34), (mx(69), 34)], G)
wire([(X(80)-5, 86.4), (X(80)-5, 44), (mx(69), 44)], K)
# GPIO25 / GPIO34
wire([(mx(33), 48), (mx(39), 48)], P)
wire([(mx(33), 26), (mx(39), 26)], G)
# valf (-) -> TIP102 C
wire([(X(24)-12, 174.2), (X(24)-12, 168), (mx(70.5), 168), (mx(70.5), 66), (mx(69), 66)], B)
txt(X(24)-12, 170.5, "−", fs=13, w='bold', c=B, ha='right')

# pin etiketleri (uc noktalarda)
for x_, y_, t, ha in ((mx(33)+1.2, 26, "GPIO34", 'left'), (mx(33)+1.2, 48, "GPIO25", 'left'), (mx(33)+1.2, 58, "GND", 'left'),
                      (mx(39)-1.2, 26, "A0", 'right'), (mx(39)-1.2, 48, "1k", 'right'), (mx(39)-1.2, 58, "GND", 'right'),
                      (mx(69)+1.2, 34, "SİNYAL", 'left'), (mx(69)+1.2, 44, "GND", 'left'), (mx(69)+1.2, 66, "C", 'left')):
    txt(x_, y_, t, fs=9, ha=ha, w='bold', bg='white')
txt(mx(20), 63, "VIN", fs=8, w='bold', bg='white')
txt(mx(62), 70.6, "OUT+", fs=7.5, w='bold', bg='white')
txt(mx(46)+1, 79.5, "IN+", fs=7.5, w='bold', bg='white')
txt(X(80)+5, 92, "kırmızı", fs=7.5, c=O, w='bold', bg='white', rotation=90)
txt(X(80), 70, "sinyal", fs=7.5, c=G, w='bold', bg='white', rotation=90)
txt(X(80)-5, 64, "siyah", fs=7.5, c=K, w='bold', bg='white', rotation=90)

# ---- kapak (ic yuzu, ters cevrilmis)
ax.add_patch(FancyBboxPatch((LX0-2, -2), IX+4, IY+4, boxstyle="round,pad=0,rounding_size=12", fc='#fbf6ea', ec='#444', lw=4, zorder=1))
txt(LX0+IX/2, -8, "KAPAK – İÇ YÜZÜ (ters çevrilmiş)", fs=15, c='#777', w='bold')
rect(lx(18.5), 7, lx(53.5), 65, '#1b3a5c', lw=2); txt(lx(36), 30, "2\" EKRAN\nST7789V\n(arka yüz)", fs=10, w='bold', c='w')
rect(lx(29), 59, lx(43), 65, '#eee', z=4); txt(lx(36), 62, "8p", fs=7.5)
BT = [(14.5, "+", "GPIO32"), (37.5, "−", "GPIO33"), (60.5, "BAŞLAT", "GPIO27")]
for x_, t, g in BT:
    ax.add_patch(Circle((lx(x_), 85), 9, fc='#ffd84d', ec='k', lw=2, zorder=4)); txt(lx(x_), 85, t, fs=12 if len(t) < 3 else 8.5, w='bold')
ax.add_patch(Circle((lx(36), 125), 7, fc='#333', ec='k', lw=2, zorder=4)); txt(lx(36), 125, "BZ", fs=8, c='w', w='bold')
txt(lx(46), 125, "BUZZER", fs=10, w='bold', ha='left')
# kapak ici kablolar -> mentese tarafindaki demet noktasi
HUB = (LX0+2, 40)
SPI = [("VCC", "3V3", R), ("GND", "GND", K), ("DIN", "GPIO23", B), ("CLK", "GPIO18", Y),
       ("CS", "GPIO5", O), ("DC", "GPIO16", G), ("RST", "GPIO17", P), ("BL", "GPIO4", '#7f7f7f')]
for i, (a, b, c) in enumerate(SPI):
    x_ = lx(29.8) + i*1.75
    ax.plot([x_, x_, lx(8)+i*1.2, HUB[0]+2], [65, 67.5, 67.5, HUB[1]+i*1.2], color=c, lw=1.6, zorder=6)
for j, (x_, t, g) in enumerate(BT):
    ax.plot([lx(x_), lx(x_), lx(5)+j*1.5, HUB[0]+2], [94, 104+j*3, 104+j*3, HUB[1]+12+j*1.5], color='#e6b800', lw=2.6, zorder=6)
    ax.plot([lx(x_)+3, lx(x_)+3, lx(4)+j*1.5], [94, 100+j*3, 100+j*3], color=K, lw=1.4, zorder=6)
    txt(lx(x_), 71.8, g + " / GND", fs=7.5, w='bold', bg='white')
ax.plot([lx(36), lx(36), lx(6), HUB[0]+2], [132, 140, 140, HUB[1]+18], color='#00a3a3', lw=2.6, zorder=6)
txt(lx(46), 133, "+ → GPIO13\n− → GND", fs=8.5, w='bold', ha='left')
# ekran pin tablosu
txt(lx(62), 14, "Ekran kablosu:", fs=10, w='bold', ha='left')
for i, (a, b, c) in enumerate(SPI):
    yy = 22 + i*5.6
    ax.plot([lx(62), lx(70)], [yy, yy], color=c, lw=4, zorder=6)
    txt(lx(72), yy, f"{a:<4} → {b}", fs=9.5, ha='left', family='DejaVu Sans Mono')
# demet: kapak -> ESP32
ax.plot([mx(10), mx(10), LX0-8, LX0-8, HUB[0]+2], [11, 4, 4, HUB[1]+8, HUB[1]+8], color='#666', lw=11, solid_capstyle='round', zorder=4, alpha=0.85)
txt((IX+LX0)/2-4, 22, "KABLO DEMETİ\n(12 tel)", fs=10, w='bold', c='#444')
txt((IX+LX0)/2-4, 48, "GPIO32/33/27\nGPIO13\nGPIO23/18/5\nGPIO16/17/4\n3V3, GND", fs=8.5, c='#333', bg='#ffffff')

# ---- alt: TIP102 detay, lejant, notlar
a2 = fig.add_axes([0.02, 0.02, 0.44, 0.235]); a2.set_xlim(0, 160); a2.set_ylim(0, 100); a2.axis('off'); a2.set_aspect('equal')
a2.add_patch(FancyBboxPatch((1, 1), 158, 96, boxstyle="round,pad=0,rounding_size=4", fc='#f1faec', ec='#5a8f3a', lw=2.5))
a2.text(80, 91, "PERTİNAKS 1 DETAYI (yakın görünüm)", ha='center', fontsize=15, weight='bold')
def w2(pts, c, lw=3):
    xs, ys = zip(*pts); a2.plot(xs, ys, color=c, lw=lw, solid_capstyle='round', zorder=2)
def res(x, y, t, vert=False):
    if vert: a2.add_patch(Rectangle((x-2, y-5), 4, 10, fc='#f5deb3', ec='k', lw=1.5, zorder=4)); a2.text(x+3, y, t, va='center', fontsize=11, weight='bold')
    else: a2.add_patch(Rectangle((x-5, y-2), 10, 4, fc='#f5deb3', ec='k', lw=1.5, zorder=4)); a2.text(x, y+4, t, ha='center', fontsize=11, weight='bold')
def lab(x, y, t, c='k', ha='center'): a2.text(x, y, t, ha=ha, va='center', fontsize=11, weight='bold', color=c)
def gnd(x, y):
    for i, ww in enumerate((4, 2.7, 1.4)): a2.plot([x-ww, x+ww], [y-i*1.3, y-i*1.3], color=K, lw=2)
# valf surucu
lab(8, 62, "GPIO25", P, 'left'); w2([(22, 62), (32, 62)], P); res(37, 62, "1k"); w2([(42, 62), (58, 62)], P)
a2.plot(50, 62, 'o', color=P, ms=6); w2([(50, 62), (50, 52)], P); res(50, 47, "10k", True); w2([(50, 42), (50, 36)], K); gnd(50, 36)
a2.add_patch(Rectangle((58, 54), 16, 16, fc='#333', ec='k', zorder=3)); a2.text(66, 62, "TIP102", color='w', ha='center', va='center', fontsize=10, weight='bold')
lab(55.5, 66, "B", P); lab(79, 72, "C", B); lab(79, 52, "E", K)
w2([(74, 68), (86, 68), (86, 76)], B); w2([(74, 56), (80, 56), (80, 44)], K); gnd(80, 44)
a2.add_patch(Rectangle((82, 76), 22, 9, fc='#2b2b2b', ec='k', zorder=3)); a2.text(93, 80.5, "VALF", color='w', ha='center', va='center', fontsize=10, weight='bold')
lab(80, 84, "−", B); w2([(104, 80.5), (112, 80.5)], R); lab(117, 80.5, "+12V", R, 'left')
# diyot
w2([(86, 72), (98, 72)], B); a2.add_patch(Rectangle((98, 70), 10, 4, fc='#222', ec='k', zorder=4)); a2.add_patch(Rectangle((106, 70), 2, 4, fc='#ddd', zorder=5))
w2([(108, 72), (110, 72), (110, 80.5)], R); a2.text(103, 62, "1N4007\n(şerit +12V)", ha='center', fontsize=9.5, weight='bold')
# sensor bolucu
lab(8, 22, "Sensör\nsinyal", G, 'left'); w2([(26, 22), (34, 22)], G); res(39, 22, "10k"); w2([(44, 22), (78, 22)], G)
a2.plot(60, 22, 'o', color=G, ms=6); w2([(60, 22), (60, 16)], G); res(60, 11.5, "20k (2×10k)", True); w2([(60, 7), (60, 5)], K); gnd(60, 5)
lab(80, 22, "GPIO34", G, 'left')
a2.text(122, 40, "Not: bölücü 4,5V'u\n~3,0V'a düşürür\n(ESP32 girişi 3,3V)", ha='center', fontsize=10, color='#333')

a3 = fig.add_axes([0.48, 0.02, 0.22, 0.235]); a3.axis('off'); a3.set_xlim(0, 100); a3.set_ylim(0, 100)
a3.add_patch(FancyBboxPatch((1, 1), 98, 96, boxstyle="round,pad=0,rounding_size=3", fc='white', ec='#999', lw=2))
a3.text(50, 90, "KABLO RENKLERİ", ha='center', fontsize=15, weight='bold')
LG = [(R, "+12V (adaptör, valf +)"), (O, "+5V (buck çıkışı)"), (K, "GND (ortak eksi)"), (B, "Valf − → TIP102 C"),
      (P, "GPIO25 → TIP102 baz"), (G, "Sensör sinyali / GPIO34"), ('#e6b800', "Buton kabloları"), ('#00a3a3', "Buzzer +"),
      ('#666', "Kapak kablo demeti"), ('#00b4ff', "Hava akış yönü")]
for i, (c, t) in enumerate(LG):
    y = 80 - i*7.6; a3.plot([8, 22], [y, y], color=c, lw=6 if c != '#00b4ff' else 3)
    a3.text(26, y, t, va='center', fontsize=11.5)

a4 = fig.add_axes([0.72, 0.02, 0.26, 0.235]); a4.axis('off'); a4.set_xlim(0, 100); a4.set_ylim(0, 100)
a4.add_patch(FancyBboxPatch((1, 1), 98, 96, boxstyle="round,pad=0,rounding_size=3", fc='#fff8d0', ec='#c9b458', lw=2))
a4.text(50, 90, "NOTLAR", ha='center', fontsize=15, weight='bold')
NT = ["Kapaktaki ekran, butonlar ve buzzer\nkablo demetiyle ESP32'ye gider.",
      "Buck çıkışını ESP32 bağlamadan önce\n5,0V'a ayarla.",
      "Butonların diğer bacağı GND'ye\n(dahili pull-up kullanılır).",
      "Tüm GND'ler ortak: adaptör −, buck −,\nESP32 GND, TIP102 E, sensör siyah.",
      "1N4007 valfe ters paralel:\nşeritli uç +12V tarafına."]
for i, t in enumerate(NT):
    a4.text(5, 78 - i*16, "• " + t, va='center', fontsize=11.5)

fig.savefig("8_KUTU_ICI_BAGLANTI.png", dpi=100)
fig.savefig("8_KUTU_ICI_BAGLANTI.pdf")
