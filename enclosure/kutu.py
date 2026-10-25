"""ESP32 tire inflator enclosure (CadQuery). Space reserved for a future G1/2 inflate valve; the small valve later becomes the exhaust valve.
Display: Waveshare 2" ST7789V LCD. Valve dimensions are parametric. One 1/4" valve now, TIP102 (TO-220) driver on perfboard,
ADS1115/buzzer/susturucu yok. Koordinat: X sağa, Y aşağı (Y=0 üst duvar), Z arkadan öne (Z=0 duvara dayanan arka yüz).
Gövde arka yüz tablada; kapak ön yüz tablada. Desteksiz PETG."""
import cadquery as cq, math
T = 0.3; W = 2.0; TABAN = 2.0
EX = 72                 # elektronik bölme iç genişliği
DIVT = 3.0
PX = 132                # pnömatik bölme iç genişliği (v6: büyük valf bobini + tahliye)
IX, IY = EX + DIVT + PX, 246
HB = 70; IZ = HB - TABAN
OX, OY = IX + 2*W, IY + 2*W
R_DIS, PAH_ARKA, KAP_PLAKA, KAP_ETEK, PAH_ON = 14, 3, 2.4, 4.0, 5
KAP_H = KAP_PLAKA + KAP_ETEK
ZK = HB + KAP_ETEK      # kapak plakası iç yüzü (montajlı)
PILOT = 2.5
def A(x, y): return (W + x, W + y)          # iç -> mutlak
KULE = [A(5, 5), A(IX-5, 5), A(5, IY-5), A(IX-5, IY-5)]
P0 = EX + DIVT           # pnömatik bölme başlangıcı (iç x)
YA, ZA = 72.0, 34.0      # ZA: hava ekseni yüksekliği (büyük valf 57 kalın, altında 2.5 boşluk)
AXX = 38.0               # hava hattı ekseni, pnömatik bölme içinde x
RED_AC = 37.0            # 3/4" redüksiyon altıgen köşe ölçüsü (32 AF) VARSAYIM
HORTUM_OD = 30.0         # 3/4" hortum dış çapı VARSAYIM

def box(x0, x1, y0, y1, z0, z1): return cq.Workplane("XY").box(x1-x0, y1-y0, z1-z0, centered=False).translate((x0, y0, z0))
def cylX(x0, x1, y, z, d): return cq.Workplane("YZ").circle(d/2).extrude(x1-x0).translate((x0, y, z))
def cylY(y0, y1, x, z, d): return cq.Workplane("XZ").circle(d/2).extrude(-(y1-y0)).translate((x, y0, z))
def cylZ(z0, z1, x, y, d): return cq.Workplane("XY").circle(d/2).extrude(z1-z0).translate((x, y, z0))
def rr(w, h, r, t): return cq.Workplane("XY").rect(w, h).extrude(t).edges("|Z").fillet(r).translate((w/2, h/2, 0))
def ax(x): return W + x
def ay(y): return W + y

# ---------------- PARÇALAR (mutlak koordinat, gerçek boyut) ----------------
def parcalar():
    p = {}; px = lambda x: ax(P0 + x); yA = ay(YA)
    # ESP32 DevKit 38 pin: 55x28x1.6 kart, üst bileşen 5, alt pin 8.5 (lehimli kablo ucu dahil 10)
    ex0, ey0 = ax(5), ay(11); ESPZ = TABAN + 11
    p["ESP32"] = box(ex0, ex0+28, ey0, ey0+55, ESPZ, ESPZ+6.6)
    p["ESP32_pin"] = box(ex0+0.5, ex0+3.5, ey0+2, ey0+53, ESPZ-9, ESPZ).union(box(ex0+24.5, ex0+27.5, ey0+2, ey0+53, ESPZ-9, ESPZ))
    p["USB_fis"] = box(ex0+14-5.5, ex0+14+5.5, -8, ey0, ESPZ+1.6+1.5-3.5, ESPZ+1.6+1.5+3.5)   # micro-USB fiş gövdesi 11x7
    # Pertinaks 30x70 (delik 2 mm içeride, 26x66), 6 mm ayak, üstte 12 mm bileşen (IRL530N yatık), altta 2 mm lehim
    bx0, by0 = ax(39), ay(3); PZ = TABAN + 6
    p["PERTINAKS"] = box(bx0, bx0+30, by0, by0+70, PZ, PZ+1.6)
    # v4: düşük bileşenler (1k, 10k, 1N4007, 10k+20k bölücü, klemensler) max 8 mm; TIP102 dik, etrafında >=3 mm hava
    p["PERT_bilesen"] = box(bx0+4, bx0+26, by0+5, by0+38, PZ+1.6, PZ+9.6).union(box(bx0+4, bx0+26, by0+60, by0+66, PZ+1.6, PZ+9.6)).union(box(bx0+5, bx0+25, by0+5, by0+65, PZ-2, PZ))
    # TIP102 TO-220 dik: bacak 4 mm, gövde 10.2x4.6x9.2, soğutma tırnağı 10.2x1.3x6.3 (delikli) yukarı
    tx, ty = bx0+15, by0+50; tz = PZ+1.6
    p["TIP102"] = box(tx-5.1, tx+5.1, ty-2.3, ty+2.3, tz+4, tz+13.2).union(box(tx-5.1, tx+5.1, ty+1.0, ty+2.3, tz+13.2, tz+19.5)).union(box(tx-3.5, tx+3.5, ty-0.5, ty+0.5, tz, tz+4))
    # Buck 17.5x12.2, 5 mm yükseklik (bobin), cep içinde
    p["BUCK_5V"] = box(ax(48), ax(65.5), ay(76), ay(88.2), TABAN+0.5, TABAN+6)
    # DC jak: Ø11.5 x 30 gövde + Ø7 x 15 körük, ağız sol duvarda
    p["DC_JAK"] = cylX(ax(0), ax(30), ay(87), TABAN+7.5, 11.5).union(cylX(ax(30), ax(45), ay(87), TABAN+7.5, 7))
    p["DC_fis"] = cylX(-14, ax(0)+0.0, ay(87), TABAN+7.5, 10).union(cylX(-14+ -20, -14, ay(87), TABAN+7.5, 4))
    # --- Hava hattı DİKEY (port ekseni Y). Giriş alt duvar (y=IY), çıkış üst duvar (y=0). Eksen x = hx, z = ZA ---
    hx = px(AXX); Y = lambda y: ay(y)
    # ORTAK (iki senaryoda da aynı): çıkış rakoru + 3/4->1/4 redüksiyon + 13 nipel + TAHLİYE T (+X kolu) + 13 nipel + SENSÖR T (+X kolu)
    p["HRAKOR_cikis"] = cylY(Y(3.5), Y(11.5), hx, ZA, RED_AC).union(cylY(-32, Y(3.5), hx, ZA, 26))
    p["HORTUM_cikis"] = cylY(-40, -0.5, hx, ZA, HORTUM_OD)
    p["RED_cikis"] = cylY(Y(11.5), Y(33.5), hx, ZA, RED_AC)
    p["T_dis"] = cylY(Y(33.5), Y(36.5), hx, ZA, 13)
    p["NIPEL_1"] = cylY(Y(36.5), Y(49.5), hx, ZA, 19.6)
    p["T_TAHLIYE"] = box(hx-11, hx+11, Y(49.5), Y(71.5), ZA-11, ZA+11)
    p["NIPEL_2"] = cylY(Y(71.5), Y(84.5), hx, ZA, 19.6)
    p["T_RAKOR"] = box(hx-11, hx+11, Y(84.5), Y(106.5), ZA-11, ZA+11)
    yt = Y(95.5)
    p["SENSOR"] = cylX(hx+11, hx+13, yt, ZA, 13).union(cylX(hx+13, hx+23, yt, ZA, 26)).union(cylX(hx+23, hx+51, yt, ZA, 22)).union(cylX(hx+51, hx+63, yt, ZA, 9))
    # giriş: 3/4" hortum rakoru (alt duvar) + 3/4" redüksiyon yuvası (şimdi 3/4->1/4, gelecekte 3/4->1/2; aynı beşik)
    p["HRAKOR_giris"] = cylY(Y(238), Y(246), hx, ZA, RED_AC).union(cylY(Y(246), OY+32, hx, ZA, 26))
    p["HORTUM_giris"] = cylY(OY+0.5, OY+40, hx, ZA, HORTUM_OD)
    p["RED_giris"] = cylY(Y(216), Y(238), hx, ZA, RED_AC)
    # ŞİMDİ: T'nin tahliye kolu 1/4 kör tapa; T altından 1/4 uzatma nipel 80 -> küçük valf (2W-025-08) -> redüksiyon
    yd = Y(60.5)
    p["SIMDI_TAPA"] = cylX(hx+11, hx+19, yd, ZA, 19.6)
    p["SIMDI_UZATMA_80"] = cylY(Y(106.5), Y(182), hx, ZA, 13.5)
    p["SIMDI_VALF_govde"] = box(hx-9.5, hx+16.5, Y(182), Y(212), ZA-11, ZA+11)
    p["SIMDI_VALF_bobin"] = cylX(hx+16.5, hx+46, Y(197), ZA, 36).union(cylX(hx+46, hx+57, Y(197), ZA, 16))
    p["SIMDI_VALF_dis"] = cylY(Y(212), Y(216), hx, ZA, 13)
    p["SIMDI_TAKOZ"] = box(hx-24, hx+15, Y(184), Y(210), TABAN+2.5, ZA-11)   # ayrı baskı valf takozu (kapak 3MF'inde)
    # GELECEK: büyük valf 2W-160-15 (G1/2) + 1/2->1/4 burç; küçük valf T'nin +X kolunda tahliye, bobin yukarı (-Y)
    p["GEL_BURC"] = cylY(Y(106.5), Y(109.5), hx, ZA, 13).union(cylY(Y(109.5), Y(114.5), hx, ZA, 30))
    p["GEL_BVALF_govde"] = box(hx-28.5, hx+28.5, Y(114.5), Y(216), ZA-28.5, ZA+28.5)
    p["GEL_BVALF_bobin"] = box(hx+28.5, hx+88.5, Y(165.25)-28.5, Y(165.25)+28.5, ZA-28.5, ZA+28.5)
    p["GEL_TNIPEL"] = cylX(hx+11, hx+24, yd, ZA, 19.6)
    p["GEL_TVALF_govde"] = box(hx+24, hx+54, yd-16.5, yd+9.5, ZA-11, ZA+11)
    p["GEL_TVALF_bobin"] = cylY(yd-16.5-29.5, yd-16.5, hx+39, ZA, 36).union(cylY(yd-57, yd-46, hx+39, ZA, 16))
    p["GEL_TUZATMA_40"] = cylX(hx+54, hx+94, yd, ZA, 13.5)
    p["GEL_SUSTURUCU"] = cylX(hx+94, ax(IX)-0.6, yd, ZA, 14)
    # ikinci TIP102 kartı (2. valf, GPIO26) - şimdi de yer ayrılmış, gelecekte takılır
    b2x, b2y = ax(39), ay(122); PZ2 = TABAN + 6
    p["GEL_PERT2"] = box(b2x, b2x+30, b2y, b2y+40, PZ2, PZ2+1.6)
    t2x, t2y = b2x+15, b2y+26; tz2 = PZ2+1.6
    p["GEL_PERT2_bilesen"] = box(b2x+4, b2x+26, b2y+4, b2y+18, tz2, tz2+8).union(box(b2x+5, b2x+25, b2y+4, b2y+36, PZ2-2, PZ2))
    p["GEL_TIP102_2"] = box(t2x-5.1, t2x+5.1, t2y-2.3, t2y+2.3, tz2+4, tz2+13.2).union(box(t2x-5.1, t2x+5.1, t2y+1.0, t2y+2.3, tz2+13.2, tz2+19.5)).union(box(t2x-3.5, t2x+3.5, t2y-0.5, t2y+0.5, tz2, tz2+4))
    # Kapak parçaları
    for (x, y, t) in BTN:
        p["BTN_"+t] = cylZ(ZK+1.5-33, ZK+1.5, ax(x), ay(y), 18).union(cylZ(ZK+1.5-4, ZK+1.5, ax(x), ay(y), 22))   # gövde Ø18 x33, somun Ø22 x4
    # Waveshare 2" LCD (montajlı): cam ön yüzü ZK'da kapak plakasına dayalı. Cam 51.2x35.7x2.4 (PCB'den taşmaz, 35 içinde varsayıldı), PCB 58x35x1.6
    lx, ly = ax(LCD[0]), ay(LCD[1])
    pcb = box(lx-LCD_W/2, lx+LCD_W/2, ly-LCD_H/2, ly+LCD_H/2, ZK-LCD_CAM-LCD_PCB, ZK-LCD_CAM)
    cam = box(lx-LCD_CAM_W/2+LCD_CAM_DX, lx+LCD_CAM_W/2+LCD_CAM_DX, ly-LCD_H/2+0.3, ly+LCD_H/2-0.3, ZK-LCD_CAM, ZK-0.0)
    kon = box(lx-LCD_W/2+1.5, lx-LCD_W/2+7.5, ly-10, ly+10, ZK-LCD_CAM-LCD_PCB-LCD_KON, ZK-LCD_CAM-LCD_PCB)   # PH2.0 8p, arka yüz, -x ucu
    p["LCD"] = pcb.union(cam).union(kon)
    p["LCD_kablo_fis"] = box(lx-LCD_W/2+2, lx-LCD_W/2+7, ly-9, ly+9, ZK-LCD_CAM-LCD_PCB-LCD_KON-8, ZK-LCD_CAM-LCD_PCB-LCD_KON-0.5)
    for i, yy in enumerate((-1, 1)):   # kelepçe çubukları (ayrı baskı), PCB uzun kenarlarına basar
        yc = ly + yy*(LCD_H/2 + KEL_OFS - KEL_B/2 + 1.25)
        p[f"LCD_kelepce{i}"] = kelepce_solid(lx, ly, yy)
    return p

BTN = [(14.5, 85, "+"), (37.5, 85, "−"), (60.5, 85, "START")]   # iç koordinat (montajlı görünüm)
LCD = (36, 34)          # Waveshare 2" LCD modül merkezi (iç koordinat)
LCD_W, LCD_H = 58.0, 35.0      # PCB dış ölçü (Waveshare wiki 58x35)
LCD_PCB, LCD_CAM = 1.6, 2.4    # PCB kalınlığı, panel kalınlığı (Waveshare panel spec 2.40) -> modül 4.0
LCD_CAM_W = 51.2               # panel boyu (spec 35.7x51.2x2.4)
LCD_CAM_DX = 0.0               # panel/aktif alanın PCB merkezine x kayması - ÖLÇ
LCD_AKT = (40.8, 30.6)         # aktif alan (wiki "Display size 30.60 x 40.80")
LCD_KON = 6.0                  # arka konnektör yüksekliği (PH2.0 8p)
KEL_OFS, KEL_B, KEL_T = 4.5, 9.0, 3.0   # kelepçe vida ekseni PCB kenarından uzaklık, çubuk genişliği, kalınlık
KEL_X = 22.0                   # kelepçe vidaları x = merkez ±22 (M3x8 sac vidası, Ø2.5 pilot)
# ----------- KABLO ROTALARI (iç x,y ; mutlak z) renk ----------
KABLOLAR = {
 "12V (kirmizi)": ("#e53935", [(30, 87, 10.5), (34, 82, 10.5), (40, 76, 12), (50, 66, 12)]),               # jak -> pertinaks 12V
 "12V buck (kirmizi)": ("#e53935", [(40, 89, 9), (46, 84, 8), (49, 82, 8)]),
 "5V (turuncu)": ("#fb8c00", [(64, 80, 9), (70, 76, 14), (70, 74, 22), (36, 70, 24), (30, 64, 18)]),                     # buck -> ESP32 VIN
 "GND (siyah)": ("#212121", [(32, 85, 8), (36, 80, 9), (45, 72, 11)]),
 "Valf kablosu (mavi)": ("#1e88e5", [(P0+38+22, 216+8, ZA), (P0+38+22, 228, 50), (P0+10, 200, 50), (P0-1.5, 180, 39), (60, 170, 30), (60, 70, 24), (54, 56, 22)]),   # valf (-) -> TIP102 C
 "Sensor kablosu (yesil)": ("#43a047", [(P0+38+63, 95.5, ZA), (P0+108, 110, 40), (P0+60, 112, 52), (P0+20, 112, 46), (P0-1.5, 112, 39), (58, 100, 30), (50, 40, 24)]),
 "2. valf kanali (gri, gelecek)": ("#9e9e9e", [(P0+124, 76, 6), (P0+100, 76, 6), (P0+8, 76, 6), (P0-1.5, 76, 12), (60, 100, 10), (54, 140, 12)]),
 "Sensor -> GPIO34 (yesil)": ("#43a047", [(50, 30, 22), (34, 30, 22), (30, 30, 22)]),
 "Baz GPIO25 -> 1k -> TIP102 B (mor)": ("#8e24aa", [(42, 45, 22), (34, 45, 22)]),
 "Butonlar (sari)": ("#fdd835", [(16, 88, ZK-31), (16, 76, 30), (37, 76, 30), (58, 76, 30), (58, 88, ZK-31), (37, 76, 30), (37, 88, ZK-31), (16, 70, 30), (12, 62, 24)]),
 "LCD SPI 8 tel (cyan)": ("#00acc1", [(11.5, 34, 39), (11.5, 44, 34), (14, 52, 27), (17, 60, 24)]),   # PH2.0 fiş -> ESP32 pinleri (23/18/5/16/17/4/3V3/GND)
}

def kelepce_cubuk(w=None):
    """Kelepçe çubuğu, baskı konumu (düz, 3 mm). Uzunluk 2*KEL_X+8, PCB kenarına 2.5 mm biner, Ø3.4 delik."""
    L_ = 2*KEL_X + 8
    c = box(-L_/2, L_/2, 0, KEL_B, 0, KEL_T)
    for sx in (-1, 1): c = c.cut(cylZ(-1, KEL_T+1, sx*KEL_X, KEL_OFS + 2.5 - 0.0, 3.4))
    return c   # y=0 kenarı PCB üstüne biner (y 0..2.5 PCB üzerinde), vida ekseni y=KEL_OFS+2.5
def kelepce_solid(lx, ly, yy):
    c = kelepce_cubuk()
    # y yerel: 0 = PCB içine 2.5 mm, vida yerel y=KEL_OFS+2.5 -> mutlak PCB kenarı +KEL_OFS
    if yy > 0: c = c.translate((lx, ly + LCD_H/2 - 2.5, 0))
    else: c = c.mirror("XZ").translate((lx, ly - LCD_H/2 + 2.5, 0))
    return c.translate((0, 0, ZK - LCD_CAM - LCD_PCB - KEL_T))

def govde():
    g = rr(OX, OY, R_DIS, HB).faces("<Z").edges().chamfer(PAH_ARKA)
    g = g.cut(rr(IX, IY, R_DIS - W, IZ + 1).translate((W, W, TABAN)))
    seats = cq.Workplane("XY")   # parçaların oturduğu yüzeyler (ayrı kontrol)
    # Ara duvar (lid dudağına 2 mm boşluk)
    d = box(ax(EX), ax(EX+DIVT), W, W+IY, TABAN, HB - 6)
    for (y, z) in ((64.5, 39), (112, 39), (180, 39), (76, 12)):          # grommet geçişleri Ø10, iki yüz 1 mm pah
        d = d.cut(cylX(ax(EX)-1, ax(EX+DIVT)+1, ay(y), z, 10))
        d = d.cut(cq.Workplane("YZ").circle(6).workplane(offset=1).circle(5).loft().translate((ax(EX)-0.01, ay(y), z)))
        d = d.cut(cq.Workplane("YZ").circle(5).workplane(offset=1).circle(6).loft().translate((ax(EX+DIVT)-1+0.01, ay(y), z)))
    for (y0, y1) in ((10, 55), (122, 170), (190, 238)):   # v6 hafifletme pencereleri (ara duvar)
        d = d.cut(box(ax(EX)-1, ax(EX+DIVT)+1, ay(y0), ay(y1), TABAN+12, HB-14))
    g = g.union(d)
    for (x, y) in KULE:
        g = g.union(cylZ(TABAN, HB, x, y, 11)).cut(cylZ(HB-15, HB+1, x, y, PILOT))
    # ESP32 rayları (pinlerin arasında, 11 yüksek), uç durdurucular + zip-tie oluğu
    ex0, ey0 = ax(5), ay(11)
    for xx in (ex0+14-9, ex0+14+6):
        r = box(xx, xx+3, ey0+2, ey0+53, TABAN, TABAN+11)
        r = r.cut(box(xx-1, xx+4, ey0+26, ey0+30, TABAN+2, TABAN+5))     # zip-tie geçişi
        g = g.union(r)
    g = g.union(box(ex0+9, ex0+19, ey0+55+T, ey0+55+T+2, TABAN, TABAN+11+4))   # alt uç durdurucu (USB karşı ucu)
    # Pertinaks ayakları 26x66, Ø7, pilot Ø2.5
    bx0, by0 = ax(39), ay(3)
    for (dx, dy) in ((2, 2), (28, 2), (2, 68), (28, 68)):
        g = g.union(cylZ(TABAN, TABAN+6, bx0+dx, by0+dy, 6)).cut(cylZ(TABAN+0.6, TABAN+7, bx0+dx, by0+dy, PILOT))
    # Buck cebi (0.5 mm taban + 3 mm çerçeve, 0.3 tolerans)
    x0, x1, y0, y1 = ax(48)-T, ax(65.5)+T, ay(76)-T, ay(88.2)+T
    g = g.union(box(x0-1.5, x1+1.5, y0-1.5, y1+1.5, TABAN, TABAN+3.5).cut(box(x0, x1, y0, y1, TABAN+0.5, TABAN+5)))
    # DC jak cebi: duvara dayalı U beşik, Ø11.5+T yatak, zip-tie oluğu; duvar deliği Ø10.5 (jak geri çıkamaz)
    jz, jy = TABAN+7.5, ay(87)
    c = box(ax(2), ax(28), jy-7.5, jy+7.5, TABAN, jz+1).cut(cylX(ax(0), ax(31), jy, jz, 11.5+2*T))
    c = c.cut(box(ax(12), ax(16), jy-9, jy+9, TABAN+0, TABAN+2))    # zip-tie
    g = g.union(c)
    g = g.cut(cylX(-1, W+1, jy, jz, 11.0))
    # Kablo kancaları (zip-tie gözlü direk Ø7, göz z 24-28)
    for (x, y) in ():
        k = cylZ(TABAN, 30, ax(x), ay(y), 7).cut(box(ax(x)-5, ax(x)+5, ay(y)-1.5, ay(y)+1.5, 25, 28))
        g = g.union(k)
    # Pnömatik oturaklar (eksen x=hx, z=ZA)
    hx = ax(P0+AXX); Y = ay; yt = ay(95.5); yd = ay(60.5)
    for (y0, y1) in ((222, 234), (16, 28)):          # redüksiyon beşikleri (Ø37+0.6)
        c = box(hx-16, hx+16, Y(y0), Y(y1), TABAN, ZA).cut(cylY(Y(y0)-1, Y(y1)+1, hx, ZA, RED_AC+2*T))
        g = g.union(c)
    g = g.union(box(hx-9, hx+9, Y(52), Y(69), TABAN, ZA-11))      # tahliye T altlığı
    g = g.union(box(hx-9, hx+9, Y(87), Y(104), TABAN, ZA-11))     # sensör T altlığı
    c = box(hx+38, hx+44, yt-15, yt+15, TABAN, ZA).cut(cylX(hx+37, hx+45, yt, ZA, 22+2*T))   # sensör beşiği
    g = g.union(c)
    # Büyük valf tabanı: 2 ray (2.5 mm), zip-tie/kelepçe olukları; küçük valf takozu ray üstüne pimle oturur
    for xx in (hx-24, hx+10):
        r = box(xx, xx+8, Y(118), Y(212), TABAN, TABAN+2.5)
        for yy in (140, 165, 190): r = r.cut(box(xx-1, xx+9, Y(yy), Y(yy+4), TABAN, TABAN+1.5))
        g = g.union(r)
    for (xx, yy) in ((hx-20, 190), (hx-20, 204)): g = g.cut(cylZ(TABAN+0.5, TABAN+3, xx, Y(yy), 3.2))   # takoz pim delikleri
    # Gelecek büyük valf için 4 kelepçe gözü (zip-tie direği) - govde kenarları dışında
    for (xx, yy) in ((hx-34, 130), (hx-34, 200), (hx+34, 125), (hx+34, 220)):
        g = g.union(cylZ(TABAN, TABAN+14, xx, Y(yy), 7).cut(box(xx-5, xx+5, Y(yy)-1.5, Y(yy)+1.5, TABAN+8, TABAN+11)))
    # Tahliye valfi (gelecek) altlığı + susturucu deliği: sağ duvar Ø16, 0.8 mm kırılabilir zar (şimdi kapalı)
    g = g.union(box(hx+28, hx+50, yd-14, yd+7, TABAN, ZA-11))
    g = g.cut(cylX(ax(IX)-0.01, OX-0.8, yd, ZA, 16))
    g = g.cut(cylX(ax(IX)-0.01, OX-0.8+0.01, yd, ZA, 16))
    # İkinci TIP102 kartı ayakları (30x40, delik 26x36)
    b2x, b2y = ax(39), ay(122)
    for (dx, dy) in ((2, 2), (28, 2), (2, 38), (28, 38)):
        g = g.union(cylZ(TABAN, TABAN+6, b2x+dx, b2y+dy, 6)).cut(cylZ(TABAN+0.6, TABAN+7, b2x+dx, b2y+dy, PILOT))
    # Kablo kanalı (2. valf): sağ bölmede tabana U klipsler hattı tahliye -> ara duvar
    for (x, y) in ((P0+100, 76), (P0+124, 76), (P0+8, 76)):
        g = g.union(box(ax(x)-4, ax(x)+4, ay(y)-4, ay(y)+4, TABAN, TABAN+9).cut(box(ax(x)-5, ax(x)+5, ay(y)-2.5, ay(y)+2.5, TABAN+2, TABAN+6)))
    # v6 hafifletme: tabanda boş bölgelere pencereler (duvara asılan arka yüz, görünmez)
    win = [(x0, x0+22, y0, y0+30) for x0 in (P0+78, P0+104) for y0 in (106, 141, 176)]
    win += [(P0+AXX-13, P0+AXX+7, 122, 182), (6, 30, 100, 130), (6, 30, 135, 165), (6, 26, 170, 190), (40, 68, 168, 190), (40, 68, 195, 240), (P0+62, P0+100, 6, 40), (P0+104, P0+128, 6, 40), (P0+90, P0+128, 84, 100)]
    for (x0, x1, y0, y1) in win: g = g.cut(box(ax(x0), ax(x1), ay(y0), ay(y1), -1, TABAN+0.01).edges("|Z").fillet(3))
    # Hortum delikleri Ø31 (alt = giriş, üst = çıkış)
    g = g.cut(cylY(OY-W-1, OY+1, hx, ZA, 31)).cut(cylY(-1, W+1, hx, ZA, 31))
    # USB erişimi (üst duvar, 13x9, yuvarlak köşe)
    uz = TABAN + 11 + 1.6 + 1.5
    g = g.cut(cq.Workplane("XZ").rect(13, 9).extrude(-(W+2)).edges("|Y").fillet(2).translate((ex0+14, -1, uz)))
    # Havalandırma: üst duvar valf bobini üstü + pertinaks üstü, sol duvar buck yanı, alt duvar elektronik
    for i in range(5):
        g = g.cut(cq.Workplane("XZ").slot2D(22, 3.2, 90).extrude(-(W+2)).translate((ax(P0+72+i*6), -1, 25)))
        g = g.cut(cq.Workplane("XZ").slot2D(22, 3.2, 90).extrude(-(W+2)).translate((ax(44+i*5), -1, 33)))
    for i in range(3):
        g = g.cut(cq.Workplane("YZ").slot2D(16, 3.2, 90).extrude(W+2).translate((-1, ay(64+i*6), 30)))
    for i in range(4):
        g = g.cut(cq.Workplane("XZ").slot2D(18, 3.2, 90).extrude(-(W+2)).translate((ax(46+i*6), OY-W-1, 32)))
    for i in range(5):
        g = g.cut(cq.Workplane("XZ").slot2D(22, 3.2, 90).extrude(-(W+2)).translate((ax(P0+72+i*6), OY-W-1, 25)))
    # Arka anahtar delikleri (2 adet, 108 mm ara) - kafa Ø9, boyun 4.6
    KH = [A(36, 200), A(P0+60, 222)]
    for (x, y) in KH:
        H = TABAN + 2.5
        g = g.union(box(x-7, x+7, y-6, y+16, 0, H+1.5))
        g = g.cut(cylZ(0, H, x, y, 9+T)).cut(box(x-2.3, x+2.3, y, y+10, 0, 1.5)).cut(box(x-(9+T)/2, x+(9+T)/2, y, y+10, 1.5, H))
    return g, KH

def kapak():
    k = rr(OX, OY, R_DIS, KAP_H).faces("<Z").edges().chamfer(PAH_ON)
    k = k.cut(rr(IX-6, IY-6, R_DIS-2*W, KAP_ETEK+1).translate((2*W, 2*W, KAP_PLAKA)))
    L = lambda x, y: (ax(x), OY - ay(y))   # iç -> kapak çerçevesi
    for (x, y) in KULE:
        lx, ly = x, OY - y
        k = k.union(cylZ(KAP_PLAKA, KAP_H, lx, ly, 11)).cut(cylZ(-0.5, KAP_H+1, lx, ly, 3.4)).cut(cylZ(-0.01, 3, lx, ly, 6.4))
    # Waveshare 2" LCD: pencere = aktif alan + 0.6, önde 45° pah; panel yuvası çerçeve; 4 kelepçe kulesi
    cx, cy = L(*LCD); cx += LCD_CAM_DX
    ow, oh = LCD_AKT[0]+0.6, LCD_AKT[1]+0.6
    k = k.cut(box(cx-ow/2, cx+ow/2, cy-oh/2, cy+oh/2, -0.5, KAP_PLAKA+1))
    k = k.cut(cq.Workplane("XY").rect(ow+6, oh+6).workplane(offset=3.0).rect(ow, oh).loft().translate((cx, cy, -0.01)))
    mx, my = L(*LCD)
    fw, fh = LCD_W + 2*T, max(LCD_H, 35.7) + 2*T   # panel 35.7 PCB'den taşabilir
    fr = box(mx-fw/2-1.6, mx+fw/2+1.6, my-fh/2-1.6, my+fh/2+1.6, KAP_PLAKA, KAP_PLAKA+LCD_CAM+1.0).cut(box(mx-fw/2, mx+fw/2, my-fh/2, my+fh/2, KAP_PLAKA-1, KAP_PLAKA+10))
    fr = fr.cut(box(mx-fw/2-3, mx-fw/2+1, my-11, my+11, KAP_PLAKA-1, KAP_PLAKA+10))   # konnektör/kablo ucu açık (-x)
    k = k.union(fr)
    zt = KAP_PLAKA + LCD_CAM + LCD_PCB      # PCB arka yüzü = kelepçe alt yüzü
    for sx in (-1, 1):
        for sy in (-1, 1):
            vx, vy = mx + sx*KEL_X, my + sy*(LCD_H/2 + KEL_OFS)
            k = k.union(cylZ(KAP_PLAKA, zt, vx, vy, 7)).cut(cylZ(KAP_PLAKA+0.8, zt+1, vx, vy, PILOT))
    for (x, y, t) in BTN:
        bx, by = L(x, y)
        k = k.cut(cylZ(-0.5, KAP_H, bx, by, 16+T)).cut(cylZ(KAP_PLAKA-1.5, KAP_PLAKA+1, bx, by, 22.6))
    dud = (cq.Workplane("XY").rect(IX-2*T, IY-2*T).rect(IX-2*T-4, IY-2*T-4).extrude(4).translate((OX/2, OY/2, KAP_H)))
    dud = dud.intersect(rr(IX-2*T, IY-2*T, R_DIS-W-T, 20).translate((W+T, W+T, 0)))
    for (x, y) in KULE: dud = dud.cut(box(x-10, x+10, OY-y-10, OY-y+10, KAP_H-1, KAP_H+6))
    # dudakta ara duvar boşluğu yok (ara duvar HB-6'da biter), hortum deliği bölgesi: dudak 4 mm, delik halkası z<=41.5 < HB-4 ok
    k = k.union(dud)
    cerc = rr(OX-2*PAH_ON-6, OY-2*PAH_ON-6, R_DIS-PAH_ON, 0.6).translate((PAH_ON+3, PAH_ON+3, -0.01))
    cerc = cerc.cut(rr(OX-2*PAH_ON-8, OY-2*PAH_ON-8, R_DIS-PAH_ON-1, 1).translate((PAH_ON+4, PAH_ON+4, -0.2)))
    k = k.cut(cerc)
    def yazi(s, x, y, b): return cq.Workplane("XY").text(s, b, 0.6, halign="center", valign="center", combine=False).mirror("YZ").translate((x, y, 0))
    for (x, y, t) in BTN:
        bx, by = L(x, y - 14); k = k.cut(yazi(t, bx, by, 4.5 if len(t) > 1 else 8))
    return k

def kapak_montaj(k):   # kapak çerçevesi -> montaj (X ekseni etrafında 180°)
    return k.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, OY, HB + KAP_H))

def hacim(a, b):
    try: return sum(s.Volume() for s in a.intersect(b).solids().vals())
    except Exception: return 0.0

def sisir(s, m=0.5):
    try: return cq.Workplane("XY").add(s.val().Shell.makeThickSolid([], m) if False else s.val().offset3D if False else None)
    except Exception: return s

if __name__ == "__main__":
    import pickle, json
    g, KH = govde(); k = kapak(); km = kapak_montaj(k)
    for n, s in (("govde", g), ("kapak", k)):
        cq.exporters.export(s, n+".stl", tolerance=0.03, angularTolerance=0.15); cq.exporters.export(s, n+".step")
        bb = s.val().BoundingBox(); print(n, round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1), "valid", s.val().isValid())
    P = parcalar()
    import os; os.makedirs("parca_modelleri", exist_ok=True)
    for a, s in P.items(): cq.exporters.export(s, f"parca_modelleri/{a}.stl", tolerance=0.1)
    kc = kelepce_cubuk(); cq.exporters.export(kc, "kelepce.stl", tolerance=0.03); cq.exporters.export(kc, "kelepce.step")
    pickle.dump({"OX": OX, "OY": OY, "HB": HB, "KAP_H": KAP_H, "KAB": {n: (c, [(ax(x), ay(y), z) for x, y, z in pts]) for n, (c, pts) in KABLOLAR.items()}}, open("_meta.pkl", "wb"))
