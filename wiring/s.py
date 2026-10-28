import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon, Circle
R,O,Y,K,B,G='#d62728','#ff8c00','#9b30d9','#111111','#1f6fd1','#1a9e3a'
def fig(title,w=16,h=10):
    f,ax=plt.subplots(figsize=(w,h),dpi=100); ax.set_xlim(0,w*10); ax.set_ylim(0,h*10); ax.axis('off')
    ax.text(w*5,h*10-4,title,ha='center',va='top',fontsize=26,weight='bold'); return f,ax
def box(ax,x,y,w,h,t,fc,fs=17,top=False,dx=0):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=1",fc=fc,ec='k',lw=2))
    ax.text(x+w/2+dx,y+h+4 if top else y+h/2,t,ha='center',va='center',fontsize=fs,weight='bold')
def pin(ax,x,y,t,side,fs=14):
    ax.plot(x,y,'o',color='k',ms=8,zorder=5)
    d={'l':(-1.5,0,'right','center'),'r':(1.5,0,'left','center'),'u':(0,2,'center','bottom'),'d':(0,-2,'center','top')}[side]
    ax.text(x+d[0],y+d[1],t,ha=d[2],va=d[3],fontsize=fs,weight='bold')
def w(ax,pts,c,lw=4):
    xs,ys=zip(*pts); ax.plot(xs,ys,color=c,lw=lw,solid_capstyle='round',zorder=2)
def res(ax,x,y,t,vert=False):
    if vert: ax.add_patch(Rectangle((x-2,y-6),4,12,fc='#f5deb3',ec='k',lw=2,zorder=4)); ax.text(x+3.5,y,t,va='center',fontsize=16,weight='bold')
    else: ax.add_patch(Rectangle((x-6,y-2),12,4,fc='#f5deb3',ec='k',lw=2,zorder=4)); ax.text(x,y+3.5,t,ha='center',fontsize=16,weight='bold')
def legend(ax,items,x,y):
    for i,(c,t) in enumerate(items):
        ax.plot([x,x+6],[y-i*5,y-i*5],color=c,lw=5); ax.text(x+8,y-i*5,t,va='center',fontsize=13)
def note(ax,x,y,t,fs=14): ax.text(x,y,t,ha='center',va='center',fontsize=fs,bbox=dict(fc='#fff8d0',ec='#c9b458',boxstyle='round,pad=0.5'))
# ---- 1 GÜÇ
f,ax=fig("1) GÜÇ BAĞLANTISI")
box(ax,5,45,22,18,"12V 2A\nAdaptör",'#fde0e0')
box(ax,38,45,18,18,"DC Jak",'#e8e8e8'); pin(ax,56,59,"+",'u'); pin(ax,56,49,"−",'d')
w(ax,[(27,59),(38,59)],R); w(ax,[(27,49),(38,49)],K)
w(ax,[(56,59),(66,59),(66,82),(150,82)],R,6); ax.text(108,85,"+12V HAT  →  valf (+)",fontsize=17,color=R,weight='bold',ha='center')
w(ax,[(56,49),(66,49),(66,18),(150,18)],K,6); ax.text(108,13,"ORTAK GND  →  her parçanın eksisi",fontsize=17,weight='bold',ha='center')
box(ax,80,40,26,28,"5V Düşürücü\n(DC-DC 5V 3A)",'#ffe9cc',15)
pin(ax,80,62,"IN+",'r'); pin(ax,80,46,"IN−",'r'); pin(ax,106,62,"OUT+",'l'); pin(ax,106,46,"OUT−",'l')
w(ax,[(66,62),(80,62)],R); w(ax,[(66,46),(80,46)],K)
box(ax,122,40,22,28,"ESP32\n+ sensör 5V",'#e3f0ff'); pin(ax,122,62,"VIN",'r'); pin(ax,122,46,"GND",'r')
w(ax,[(106,62),(122,62)],O); w(ax,[(106,46),(114,46),(114,18)],K)
w(ax,[(118,46),(122,46)],K); w(ax,[(114,46),(118,46)],K)
ax.text(114,65,"5V",color=O,fontsize=16,weight='bold',ha='center')
note(ax,95,30,"ÖNEMLİ: ESP32'yi bağlamadan önce\ndüşürücü çıkışını ölç (5,0V olmalı)")
legend(ax,[(R,'+12V'),(O,'+5V'),(K,'GND')],5,92)
f.savefig('1_guc.png',bbox_inches='tight'); plt.close(f)
# ---- 2 VALF + TIP102
f,ax=fig("2) VALF + TIP102 SÜRÜCÜ",16,11.5)
box(ax,4,44,22,24,"ESP32",'#e3f0ff'); pin(ax,26,60,"GPIO25",'l'); pin(ax,26,50,"GND",'l')
w(ax,[(26,60),(42,60)],B); res(ax,48,60,"1K"); w(ax,[(54,60),(70,60),(70,30),(80,30),(80,34)],B)
ax.add_patch(Rectangle((76,64),24,6,fc='#bbbbbb',ec='k',lw=2)); ax.add_patch(Circle((88,67),1.8,fc='w',ec='k'))
ax.add_patch(Rectangle((76,46),24,18,fc='#333333',ec='k',lw=2)); ax.text(88,57,"TIP102",color='w',ha='center',va='center',fontsize=17,weight='bold')
for xl,t in [(80,'B'),(88,'C'),(96,'E')]:
    ax.add_patch(Rectangle((xl-1,34),2,12,fc='#cccccc',ec='k')); ax.text(xl,49,t,ha='center',va='center',fontsize=20,weight='bold',color='#ffd24d')
ax.text(88,74,"önden görünüm (yazılı yüz sana bakıyor)\nsoldan sağa: B - C - E",ha='center',fontsize=13,style='italic')
w(ax,[(70,44),(60,44),(60,34)],B); ax.plot(70,44,'o',color=B,ms=9,zorder=6); res(ax,60,27,"10K",True); w(ax,[(60,21),(60,10)],K)
w(ax,[(96,34),(96,28)],K,4)
for i,ww in enumerate((6,4,2)): ax.plot([96-ww,96+ww],[28-i*1.5,28-i*1.5],color=K,lw=3)
ax.text(103,26,"GND",fontsize=15,weight='bold',va='center')
w(ax,[(26,50),(34,50),(34,10),(70,10)],K,6)
for i,ww in enumerate((6,4,2)): ax.plot([70-ww,70+ww],[8-i*1.5,8-i*1.5],color=K,lw=3)
ax.text(76,8,"GND",fontsize=15,weight='bold',va='center')
ax.text(122,5,"GND işaretlerinin hepsi aynı hat (ORTAK GND)",fontsize=14,weight='bold',ha='center')
w(ax,[(88,34),(88,22),(118,22),(118,40)],G)
box(ax,110,40,20,24,"VALF\n12V",'#fde0e0'); pin(ax,118,40,"−",'r'); pin(ax,118,64,"+",'r')
w(ax,[(118,64),(118,92),(152,92)],R,6); ax.text(142,95,"+12V",color=R,fontsize=17,weight='bold')
w(ax,[(118,30),(142,30),(142,44)],G,3); w(ax,[(118,84),(142,84),(142,60)],R,3)
ax.add_patch(Rectangle((139,44),6,16,fc='#222',ec='k')); ax.add_patch(Rectangle((139,55),6,3,fc='#ddd',ec='k'))
ax.text(147,52,"1N4007\nçizgi yukarı\n(+12V tarafı)",fontsize=13,va='center')
note(ax,58,84,"Tek valf (sadece şişirme).\nİndirme: çakmaktaki düğmeyle elle.",15)
legend(ax,[(R,'+12V'),(B,'ESP32 sinyali → B'),(G,'C → valf (−)'),(K,'GND (E)')],4,104)
f.savefig('2_valf.png',bbox_inches='tight'); plt.close(f)
# ---- 3 SENSÖR
f,ax=fig("3) BASINÇ SENSÖRÜ + BÖLÜCÜ → GPIO34",16,10)
box(ax,4,30,24,36,"ESP32",'#e3f0ff',top=True); pin(ax,28,56,"GPIO34",'l'); pin(ax,28,38,"GND",'l')
w(ax,[(28,56),(78,56)],B); ax.plot(66,56,'o',color=B,ms=9,zorder=6)
w(ax,[(66,56),(66,46)],B); res(ax,66,38,"20K\n(2×10K seri)",True); w(ax,[(66,32),(66,12)],K)
res(ax,86,56,"10K"); w(ax,[(92,56),(112,56)],B)
box(ax,112,34,30,32,"Basınç\nSensörü\n200 PSI",'#fff6d5',15,dx=6)
pin(ax,112,62,"Kırmızı (+5V)",'r',12); pin(ax,112,56,"Sinyal",'r',12); pin(ax,112,42,"Siyah (GND)",'r',12)
w(ax,[(112,62),(104,62),(104,80),(150,80)],O); ax.text(140,83,"+5V (düşürücüden)",color=O,fontsize=15,weight='bold',ha='center')
w(ax,[(112,42),(104,42),(104,12)],K); w(ax,[(28,38),(40,38),(40,12)],K); w(ax,[(40,12),(150,12)],K,6); ax.text(140,7,"ORTAK GND",fontsize=16,weight='bold')
note(ax,45,80,"4,5V → 3,0V'a düşer (ESP32 max 3,3V)\nSinyal ASLA direkt GPIO'ya bağlanmaz",14)
legend(ax,[(O,'+5V'),(B,'sinyal'),(K,'GND')],126,30)
f.savefig('3_sensor.png',bbox_inches='tight'); plt.close(f)
# ---- 4 BUTON
f,ax=fig("4) BUTONLAR",15,10.5)
box(ax,6,14,24,58,"ESP32",'#e3f0ff',top=True); pin(ax,18,14,"GND",'u')
for i,(gp,t) in enumerate([("GPIO32","+"),("GPIO33","−"),("GPIO27","BAŞLAT")]):
    y=62-i*18; pin(ax,30,y,gp,'l'); w(ax,[(30,y),(70,y)],B)
    ax.add_patch(Circle((80,y),7,fc='#ffd24d',ec='k',lw=2)); ax.text(80,y,t,ha='center',va='center',fontsize=15 if len(t)>1 else 24,weight='bold')
    w(ax,[(90,y),(110,y)],K); pin(ax,70,y,"",'u'); pin(ax,90,y,"",'u')
w(ax,[(110,62),(110,8),(18,8),(18,14)],K,5)
note(ax,80,84,"Butonun bir ayağı GPIO'ya, diğeri GND'ye.\nEk direnç GEREKMEZ (dahili pull-up açık).",15)
legend(ax,[(B,'buton GPIO'),(K,'GND')],120,40)
f.savefig('4_butonlar.png',bbox_inches='tight'); plt.close(f)
# ---- 5 EKRAN
f,ax=fig("5) EKRAN: 2\" LCD ST7789V (Waveshare)",16,12)
box(ax,4,8,26,100,"ESP32",'#e3f0ff',top=True)
box(ax,122,8,30,100,"2\" LCD\nST7789V",'#d8e6ff',18)
P=[("VCC","3V3",'#d62728',"3,3V"),("GND","GND",K,"GND"),("DIN","GPIO23",B,"veri"),("CLK","GPIO18",'#f2c500',"saat"),
   ("CS","GPIO5",'#ff8c00',"seçim"),("DC","GPIO16",G,"komut/veri"),("RST","GPIO17",'#8e24aa',"reset"),("BL","GPIO4",'#7f7f7f',"ışık")]
for i,(lp,ep,c,an) in enumerate(P):
    y=100-i*12
    w(ax,[(30,y),(122,y)],c,6)
    ax.plot(30,y,'o',color='k',ms=10,zorder=5); ax.plot(122,y,'o',color='k',ms=10,zorder=5)
    ax.text(32,y+1.2,ep,ha='left',va='bottom',fontsize=19,weight='bold')
    ax.text(120,y+1.2,lp,ha='right',va='bottom',fontsize=19,weight='bold')
    ax.text(76,y+1.2,an,ha='center',va='bottom',fontsize=13,color='#444')
note(ax,80,2,"VCC mutlaka 3,3V (5V değil).",15)
f.savefig('5_ekran.png',bbox_inches='tight'); plt.close(f)
# ---- 6 PNÖMATİK HAT (gerçek hat, kutu v7)
f,ax=fig("6) PNÖMATİK HAT – hava soldan sağa",20,8)
A='#5b8fd6'
parts=[("GİRİŞ\nBARB",'#f3d27a',"sol duvar\nyarığından\ndışarı"),("VALF\n2W-025-08",'#fde0e0',"bobin\nyukarı"),("HIZLI\nGEÇME",'#cfd8dc',""),
       ("PU\nHORTUM",'#bbdefb',""),("HIZLI\nGEÇME T",'#bdbdbd',"yan kol:\nSENSÖR"),("PU\nHORTUM",'#bbdefb',""),("HIZLI\nGEÇME",'#cfd8dc',""),("ÇIKIŞ\nBARB",'#f3d27a',"hortum Ø17\ndelikten\niçeri girer")]
x=6; bw=19; gap=5
for i,(t,c,alt) in enumerate(parts):
    box(ax,x,32,bw,16,t,c,13)
    if alt: note(ax,x+bw/2,66 if i==4 else 14,alt,12)
    if i==4: w(ax,[(x+bw/2,49),(x+bw/2,58)],K,3)
    if i<len(parts)-1: ax.annotate('',xy=(x+bw+gap-0.5,40),xytext=(x+bw+0.5,40),arrowprops=dict(arrowstyle='->',color=A,lw=4))
    x+=bw+gap
note(ax,100,4,"Sensör kolu: düz hızlı geçme → adaptör → redüksiyon (teflonlu) → sensör. Valf üstündeki ok hava yönünde olmalı.",13)
f.savefig('6_pnomatik.png',bbox_inches='tight'); plt.close(f)
# ---- 7 BUZZER
f,ax=fig("7) BUZZER (bitiş sesi)",15,9)
box(ax,6,20,26,44,"ESP32",'#e3f0ff',top=True); pin(ax,32,54,"GPIO13",'l'); pin(ax,32,30,"GND",'l')
w(ax,[(32,54),(96,54)],B)
ax.add_patch(Circle((108,42),13,fc='#333',ec='k',lw=2)); ax.add_patch(Circle((108,42),3,fc='#777',ec='k'))
ax.text(108,61,"BUZZER",ha='center',fontsize=18,weight='bold')
pin(ax,96,54,"+",'u'); pin(ax,96,30,"−",'d')
w(ax,[(32,30),(96,30)],K,5)
note(ax,75,8,"Uzun bacak / kırmızı kablo (+) GPIO13'e, kısa bacak (−) GND'ye.\nAktif veya pasif buzzer olur. Bitişte 3 kısa + 1 uzun bip.",14)
legend(ax,[(B,'GPIO13 sinyal'),(K,'GND')],120,82)
f.savefig('7_buzzer.png',bbox_inches='tight'); plt.close(f)
