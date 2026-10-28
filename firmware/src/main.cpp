// OTA (kablosuz güncelleme) şifresiz: Wi-Fi ağına bağlanan herkes yükleyebilir.
// OTA is password-free: anyone on the device's Wi-Fi can upload firmware.
/*
 * ESP32 Otomatik Lastik Şişirme İstasyonu
 * Kart    : ESP32 DevKit (ESP-WROOM-32)
 * Valf    : 12V NC solenoid (şimdi 2W-025-08), TIP102 ile sürülür (GPIO25 HIGH = açık)
 *           GPIO25 -> 1K -> B, B -> 10K -> GND, E -> GND, C -> valf(-), valf(+) -> 12V, 1N4007 valfe ters paralel
 * Tahliye : İsteğe bağlı 2. valf GPIO26 (TAHLIYE_VALFI=1 ile açılır, varsayılan kapalı)
 * Sensör  : 0.5-4.5V, 5V beslemeli, 200 PSI (13,79 bar). 10k (üst) + 20k (alt) bölücü -> GPIO34
 * Ekran   : Waveshare 2" ST7789V 240x320 (DIN 23, CLK 18, CS 5, DC 16, RST 17, BL 4)
 * Butonlar: GPIO32 "+", GPIO33 "−", GPIO27 BAŞLAT/DURDUR (uzun bas: birim kPa/bar/psi)
 * Buzzer  : GPIO13 (+) / GND (−). Aktif ya da pasif fark etmez (2,7 kHz PWM).
 * Arayüz  : LovyanGFX + gömülü VLW yumuşak fontlar (tools/vlw_uret.py ile üretilir)
 */
#include <Arduino.h>
#include <SPI.h>
#include <LovyanGFX.hpp>
#include "fontlar.h"
#include <WiFi.h>
#include <DNSServer.h>
#include <sys/time.h>
#include <ArduinoOTA.h>
#include <WebServer.h>
#include <Update.h>
#include <Preferences.h>
#include <time.h>
#include "panel.h"

// ---------------- ŞİŞİRME PARAMETRELERİ (adaptif puls + test modu) ----------------
// Aşağıdaki 6 değer Preferences'tan okunur, /param ile değiştirilebilir (varsayılanlar burada)
uint32_t PULS_ILK_MS = 1500;    // ilk puls kısa: havası olan lastikte hedefi aşmasın
uint32_t PULS_MIN_MS = 300;
uint32_t PULS_MAX_MS = 15000;   // boş lastikte ilk puls bu kadar uzun olabilir
uint32_t OTURMA_MS   = 800;     // puls sonrası ölçüm beklemesi (700-1000)
float ADAPTIF_KATSAYI = 0.8f;   // sonraki puls = kalan/rate * katsayı
float BITIS_PSI       = 0.3f;   // hedefe bu kadar kala bitir
#define OLCUM_ORNEK      10     // oturmadan sonra ortalaması alınan okuma sayısı
#define ARTIS_ESIK_PSI   0.05f  // bundan az artış = "artmadı"
#define ARTISSIZ_MAX     3      // arka arkaya artışsız puls -> HAVA YOK / KACAK
uint32_t TEST_PULS_MS = 3000;   // /test?puls= ile değişir (kaydedilmez)
#define TEST_OTURMA_MS   1000
float TEST_HEDEF_PSI = 32.0f;   // /test?hedef= ile değişir (kaydedilmez)
#define PSI_BAR          14.5038f
// Öğrenilen şişirme hızı (psi/sn). İlk puls = kalan / hız * ILK_KATSAYI. Her işte güncellenir, kaydedilir.
float ogrRate = 1.92f;   // varsayılan (örnek): 0->32 psi ilk puls 10 sn, 10 psi -> ~7 sn; sonra ölçerek öğrenir
bool ogrVar = false;     // hız en az bir kez ölçüldü mü
#define ILK_KATSAYI      0.9f    // ilk puls (0 psi -> 32: ~15 sn)
#define YAKLASMA_PSI     7.0f    // hedefin bu kadar altına kadar büyük pulslar (32 hedefte 25 psi), sonra kısa/sık
#define INCE_MAX_MS      2000    // ince bölgede en uzun puls
#define YAKIN_PSI        3.0f    // hedefe bu kadar kala pulslar ekstra kısalır

#ifndef TAHLIYE_VALFI
#define TAHLIYE_VALFI 0   // 1 yapılırsa aşırı basınçta otomatik tahliye
#endif

// ---------------- PİNLER ----------------
const int PIN_VALF_SIS = 25;
const int PIN_VALF_BOS = 26;
const int PIN_SENSOR   = 34;
const int PIN_BTN_ART  = 32;
const int PIN_BTN_AZ   = 33;
const int PIN_BTN_BAS  = 27;
const int PIN_BUZZER   = 13;

// ---------------- WiFi / OTA ----------------
const char *AP_ADI    = "Lastik-Sisirme";
const char *AP_SIFRE  = "123456789";      // Wi-Fi şifresi (varsayılan, istersen değiştir)
const char *HOST_ADI  = "lastik-sisirme";
const int TFT_CS = 5, TFT_DC = 16, TFT_RST = 17, TFT_BL = 4;  // MOSI 23, SCK 18 (donanım SPI)

// ---------------- KALİBRASYON ----------------
const float BOLUCU_ORAN   = 20.0f / 30.0f;  // 20k / (10k + 20k)
const float SENSOR_V_MIN  = 0.5f;           // 0 bar çıkışı (V)
const float SENSOR_V_MAX  = 4.5f;           // tam skala çıkışı (V)
const float SENSOR_BAR_MAX = 13.79f;        // 200 PSI
float sifirOfset = 0.0f;
float kalK = 1.0f;                          // kazanç düzeltmesi: bar = (ham - ofset) * kalK
float sonHamMv = 0, sonHamBar = 0;          // /ham için son okuma                    // açılışta ölçülen sıfır hatası (bar)

// ---------------- GÜVENLİK / KONTROL ----------------
const float MUTLAK_MAX_BAR = 10.0f;    // aşılırsa valf kapanır, hata
const float HEDEF_MIN_BAR  = 0.5f;
const float HEDEF_MAX_BAR  = 9.0f;
const float TOLERANS_BAR   = 0.05f;
const float FAZLA_BAR      = 0.15f;    // hedefin bu kadar üstü = aşırı basınç uyarısı
const float SENSOR_KOPUK_V = 0.3f;
const float SENSOR_KISA_V  = 4.8f;
const uint32_t TOPLAM_MAX_MS = 5UL * 60UL * 1000UL;

// ---------------- NESNELER / DURUM ----------------
class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 panel; lgfx::Bus_SPI bus; lgfx::Light_PWM isik;
public:
  LGFX() {
    { auto c = bus.config(); c.spi_host = VSPI_HOST; c.spi_mode = 0; c.freq_write = 40000000; c.freq_read = 16000000;
      c.pin_sclk = 18; c.pin_mosi = 23; c.pin_miso = -1; c.pin_dc = TFT_DC; c.dma_channel = SPI_DMA_CH_AUTO; bus.config(c); panel.setBus(&bus); }
    { auto c = panel.config(); c.pin_cs = TFT_CS; c.pin_rst = TFT_RST; c.pin_busy = -1;
      c.panel_width = 240; c.panel_height = 320; c.offset_x = 0; c.offset_y = 0; c.offset_rotation = 0;
      c.readable = false; c.invert = true; c.rgb_order = false; c.dlen_16bit = false; c.bus_shared = false; panel.config(c); }
    { auto c = isik.config(); c.pin_bl = TFT_BL; c.invert = false; c.freq = 44100; c.pwm_channel = 7; isik.config(c); panel.setLight(&isik); }
    setPanel(&panel);
  }
};
LGFX tft;
Preferences ayar;
enum Durum { BEKLE, SISIR, OTUR, BOSALT, BITTI, HATA };
Durum durum = BEKLE;
enum Birim { KPA, BAR, PSI };
uint8_t birim = BAR;
float hedefBar = 2.2f, basinc = 0, pulsOncesi = 0;
bool sensorOk = true;
uint32_t durumT = 0, basT = 0, pulsSure = PULS_ILK_MS, bitisMs = 0;
bool testMod = false; uint16_t pulsNo = 0;
uint8_t yukselmez = 0;
const char *hataMsj = "";

// ---------------- LASTİK TAKILI KONTROLÜ ----------------
const float LASTIK_MIN_BAR = 0.1f;
uint32_t lastikUyariT = 0;   // 0 değilse "LASTİK TAKILI MI?" gösteriliyor
bool lastikUyari() { return lastikUyariT && millis() - lastikUyariT < 3000; }

// ---------------- VALF ----------------
uint32_t valfAcikT = 0, havaGunMs = 0, havaTopMs = 0;   // valfin açık kaldığı süre (RAM; TAMAM'da yazılır)
void havaSay() { if (valfAcikT) { uint32_t d = millis() - valfAcikT; havaGunMs += d; havaTopMs += d; valfAcikT = 0; } }
void valfKapat() { havaSay(); digitalWrite(PIN_VALF_SIS, LOW); if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, LOW); }
void sisirAc()   { if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, LOW); delay(5); digitalWrite(PIN_VALF_SIS, HIGH); if (!valfAcikT) valfAcikT = millis(); }
void bosaltAc()  { digitalWrite(PIN_VALF_SIS, LOW); delay(5); if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, HIGH); }

// ---------------- SENSÖR ----------------
// 16 örnek ortalaması; analogReadMilliVolts ESP32'nin fabrika ADC kalibrasyonunu kullanır.
bool basincOku(float &bar) {
  uint32_t top = 0;
  for (int i = 0; i < 64; i++) top += analogReadMilliVolts(PIN_SENSOR);
  float v = (top / 64.0f) / 1000.0f / BOLUCU_ORAN;  // gerçek sensör gerilimi
  sonHamMv = v * 1000.0f;
  sonHamBar = (v - SENSOR_V_MIN) * SENSOR_BAR_MAX / (SENSOR_V_MAX - SENSOR_V_MIN);   // kalibrasyonsuz
  if (v < SENSOR_KOPUK_V || v > SENSOR_KISA_V) return false;
  bar = (sonHamBar - sifirOfset) * kalK;
  if (bar < 0) bar = 0;
  return true;
}

// ---------------- BİRİM ----------------
float cevir(float b) { return birim == KPA ? b * 100.0f : birim == PSI ? b * 14.5038f : b; }
const char *birimAd() { return birim == KPA ? "kPa" : birim == PSI ? "psi" : "bar"; }
void yaz(char *s, float b) {
  if (birim == KPA) sprintf(s, "%.0f", cevir(b));
  else if (birim == PSI) sprintf(s, "%.1f", cevir(b));
  else sprintf(s, "%.2f", b);
}

// ---------------- BUZZER (bloklamayan kuyruk) ----------------
// Her adım: çalma ms, sessizlik ms. 2,7 kHz %50 PWM: pasif buzzer öter, aktif buzzer da ses verir.
struct Bip { uint16_t on, off; };
Bip bipQ[16]; uint8_t bipBas = 0, bipSon = 0; uint32_t bipT = 0; bool bipCaliyor = false, bipSessiz = false;
void bipEkle(uint8_t adet, uint16_t on, uint16_t off) {
  for (uint8_t i = 0; i < adet; i++) { uint8_t n = (bipSon + 1) % 16; if (n == bipBas) return; bipQ[bipSon] = {on, off}; bipSon = n; }
}
void bipSustur() { bipBas = bipSon; ledcWriteTone(PIN_BUZZER, 0); bipCaliyor = bipSessiz = false; }
void bipIsle() {
  uint32_t n = millis();
  if (bipCaliyor) { if (n - bipT >= bipQ[bipBas].on) { ledcWriteTone(PIN_BUZZER, 0); bipCaliyor = false; bipSessiz = true; bipT = n; } return; }
  if (bipSessiz) { if (n - bipT < bipQ[bipBas].off) return; bipSessiz = false; bipBas = (bipBas + 1) % 16; }
  if (bipBas != bipSon) { ledcWriteTone(PIN_BUZZER, 2700); bipCaliyor = true; bipT = n; }
}
void sesTik()   { bipEkle(1, 30, 20); }
void sesBasla() { bipEkle(1, 120, 60); }
void sesTamam() { bipEkle(3, 250, 150); bipEkle(1, 700, 50); }   // bitti: 3 kısa + 1 uzun, belirgin
void sesHata()  { bipSustur(); bipEkle(3, 400, 200); }
void sesBirim() { bipEkle(2, 70, 70); }

// ---------------- EKRAN ----------------
// Düzen: "Büyük dijital kart". Sabit çerçeve bir kez çizilir,
// değişen alanlar ayrı sprite'larda hazırlanıp tek seferde basılır (titreme yok).
#define RGB(r,g,b) ((uint16_t)((((r)&0xF8)<<8)|(((g)&0xFC)<<3)|((b)>>3)))
const uint16_t C_ARKA = RGB(8,10,14), C_KART = RGB(18,24,34), C_CYAN = RGB(0,200,255), C_CIZGI = RGB(0,90,130),
               C_GRI = RGB(120,140,160), C_BEYAZ = RGB(255,255,255), C_SARI = RGB(255,200,0),
               C_YESIL = RGB(30,170,80), C_YESILY = RGB(80,220,120), C_KIRMIZI = RGB(220,40,40),
               C_KIRMIZIY = RGB(255,80,80), C_TURUNCU = RGB(240,130,0), C_MOR = RGB(220,90,255), C_IMZA = RGB(230,230,240);
// Kart geometrisi (240x320)
const int KX = 12, KY = 42, KW = 217, KH = 129;          // büyük kart
const int SX[2] = {12, 124}, SY = 180, SW = 105, SH = 49; // küçük kartlar
const int DX = 12, DY = 238, DW = 217, DH = 39;           // durum butonu
LGFX_Sprite spWifi(&tft), spEt(&tft), spRakam(&tft), spBirim(&tft), spDeger(&tft), spDurum(&tft);

void spHazirla(LGFX_Sprite &s, int w, int h) { s.setColorDepth(16); s.createSprite(w, h); }
void sabitCiz() {
  tft.fillScreen(C_ARKA);
  tft.loadFont(f_baslik); tft.setTextDatum(top_center); tft.setTextColor(C_CYAN);
  tft.drawString("LASTİK ŞİŞİRME", 120, 6); tft.unloadFont();
  tft.drawFastHLine(20, 32, 201, C_CIZGI);
  tft.fillSmoothRoundRect(KX, KY, KW, KH, 14, C_CYAN);
  tft.fillSmoothRoundRect(KX + 1, KY + 1, KW - 2, KH - 2, 13, C_KART);
  tft.loadFont(f_etiket); tft.setTextColor(C_GRI);
  for (int i = 0; i < 2; i++) {
    tft.fillSmoothRoundRect(SX[i], SY, SW, SH, 10, C_KART);
    tft.drawString(i ? "FARK" : "HEDEF", SX[i] + 52, 186);
  }
  tft.unloadFont();
}
// Kart içi sprite: arka plan kart rengi, ortalı yazı
void yaziSprite(LGFX_Sprite &s, const uint8_t *font, const char *t, uint16_t renk, uint16_t arka, int x, int y, int yOfs) {
  s.fillSprite(arka); s.loadFont(font); s.setTextDatum(top_center); s.setTextColor(renk);
  s.drawString(t, s.width() / 2, yOfs); s.unloadFont(); s.pushSprite(x, y);
}
// Etiket satırı: normalde "BASINÇ"; test modunda puls/süre bilgisi (küçük, mor)
void etiketCiz(const char *t, uint16_t renk) { yaziSprite(spEt, f_etiket, t, renk, C_KART, 20, 48, 2); }
void rakamCiz(const char *t, uint16_t renk)  { yaziSprite(spRakam, f_rakam, t, renk, C_KART, 16, 66, 4); }
void birimCiz()                              { yaziSprite(spBirim, f_kucuk, birimAd(), C_CYAN, C_KART, 16, 138, 2); }
void kucukDegerCiz(int i, const char *t, uint16_t renk) { yaziSprite(spDeger, f_kalin, t, renk, C_KART, SX[i] + 4, 199, 1); }
void durumCiz(const char *t, uint16_t renk) {
  spDurum.fillSprite(C_ARKA); spDurum.fillSmoothRoundRect(0, 0, DW, DH, 12, renk);
  spDurum.loadFont(f_kalin); spDurum.setTextDatum(top_center); spDurum.setTextColor(C_BEYAZ);
  spDurum.drawString(t, DW / 2, 7); spDurum.unloadFont(); spDurum.pushSprite(DX, DY);
}
void ekranBaslat() {
  tft.init(); tft.setRotation(2); tft.setBrightness(255);
  spHazirla(spEt, 200, 18); spHazirla(spRakam, 208, 70); spHazirla(spBirim, 208, 28);
  spHazirla(spDeger, 97, 28); spHazirla(spDurum, DW, DH); spHazirla(spWifi, 128, 20);
  sabitCiz();
}
// Açılış mesajı (SIFIR KAYDEDİLDİ / TEST MODU) yeni stilde durum butonunda
void mesaj(const char *t, uint16_t renk) { durumCiz(t, renk); }

// Basınç rakamı: en fazla 4 kez/sn ve yalnız değişince
void degerCiz(bool zorla) {
  static char onceki[16] = ""; static uint16_t oncekiR = 0; static uint32_t sonT = 0; static float gosterilen = -1;
  if (!zorla && millis() - sonT < 250) return;
  if (zorla || gosterilen < 0 || fabsf(basinc - gosterilen) >= 0.02f) gosterilen = basinc;
  char a[16]; if (sensorOk) yaz(a, gosterilen); else strcpy(a, "---");
  bool fazla = sensorOk && basinc > hedefBar + FAZLA_BAR;
  uint16_t r = fazla ? C_KIRMIZIY : C_BEYAZ;
  if (!zorla && !strcmp(a, onceki) && r == oncekiR) return;
  sonT = millis(); strcpy(onceki, a); oncekiR = r;
  rakamCiz(a, r);
  // FARK = basınç − hedef (seçili birimde, işaretli)
  char f[16];
  if (!sensorOk) { strcpy(f, "---"); kucukDegerCiz(1, f, C_GRI); return; }
  float fb = gosterilen - hedefBar, fv = cevir(gosterilen) - cevir(hedefBar);
  if (birim == KPA) snprintf(f, sizeof f, "%+.0f", fv); else if (birim == PSI) snprintf(f, sizeof f, "%+.1f", fv); else snprintf(f, sizeof f, "%+.2f", fv);
  if (!strncmp(f + 1, "0.0", 3) && atof(f + 1) == 0) f[0] = ' ';  // "-0.0" görünmesin
  uint16_t fr = fabsf(fb) <= TOLERANS_BAR ? C_YESILY : fb > FAZLA_BAR ? C_KIRMIZIY : fb > 0 ? C_SARI : C_CYAN;
  kucukDegerCiz(1, f, fr);
}
void ekranCiz() {
  static char onceki[64] = "";
  char h[16], anah[64];
  yaz(h, hedefBar);
  uint32_t sn = ((durum == BITTI || durum == HATA) ? bitisMs : millis() - basT) / 1000;
  if (!testMod) sn = 0;
  bool fazla = sensorOk && basinc > hedefBar + FAZLA_BAR; bool lu = lastikUyari();
  snprintf(anah, sizeof anah, "%s|%d|%d|%d|%d|%d|%u|%lu|%d", h, durum, birim, sensorOk, testMod, fazla, pulsNo, (unsigned long)sn, lu);
  if (!strcmp(anah, onceki)) { degerCiz(false); return; }
  strcpy(onceki, anah);
  if (testMod) {
    char t[40]; snprintf(t, sizeof t, "TEST • puls %u • %s %lu sn", pulsNo, durum == BITTI ? "toplam" : "süre", (unsigned long)sn);
    etiketCiz(t, C_MOR);
  } else etiketCiz("BASINÇ", C_GRI);
  birimCiz();
  kucukDegerCiz(0, h, C_SARI);
  degerCiz(true);
  const char *d = "HAZIR"; uint16_t r = C_YESIL;
  switch (durum) {
    case SISIR: case OTUR: d = "ŞİŞİRİLİYOR"; r = RGB(0,150,200); break;
    case BOSALT: d = "BOŞALTILIYOR"; r = C_TURUNCU; break;
    case BITTI: d = "TAMAM"; r = C_YESIL; break;
    case HATA: d = hataMsj; r = C_KIRMIZI; break;
    default: if (fazla) { d = "FAZLA! HAVA BOŞALT"; r = C_KIRMIZI; } break;
  }
  if (!sensorOk && durum != HATA) { d = "SENSÖR HATASI"; r = C_KIRMIZI; }
  if (lu && durum != HATA) { d = "LASTİK TAKILI MI?"; r = C_TURUNCU; }
  durumCiz(d, r);
}

// ---------------- SAYAÇ (Preferences, yalnız TAMAM ve gün değişiminde yazılır) ----------------
uint32_t sayBugun = 0, sayToplam = 0; int32_t gunNo = -1;   // gunNo: 1970'ten beri İstanbul günü
uint16_t son7[7] = {0};                                      // [0]=bugün ... [6]=6 gün önce
bool saatVar() { time_t t = time(nullptr); return t > 1700000000; }
int32_t bugunNo() { return (int32_t)((time(nullptr) + 3 * 3600) / 86400); }
void sayacKaydet() {
  ayar.putUInt("sBug", sayBugun); ayar.putUInt("sTop", sayToplam); ayar.putInt("gun", gunNo);
  ayar.putUInt("hGun", havaGunMs / 1000); ayar.putUInt("hTop", havaTopMs / 1000); ayar.putBytes("s7", son7, sizeof son7);
}
void sayacYukle() {
  sayBugun = ayar.getUInt("sBug", 0); sayToplam = ayar.getUInt("sTop", 0); gunNo = ayar.getInt("gun", -1);
  havaGunMs = ayar.getUInt("hGun", 0) * 1000UL; havaTopMs = ayar.getUInt("hTop", 0) * 1000UL; ayar.getBytes("s7", son7, sizeof son7);
}
// Gün değişimi yalnız telefon saati geldiyken; saat yoksa son tarih korunur, günlük sayaç sıfırlanmaz
void gunKontrol() {
  if (!saatVar()) return;
  int32_t b = bugunNo(); if (b == gunNo) return;
  if (gunNo >= 0 && b > gunNo) {
    int32_t fark = min<int32_t>(b - gunNo, 7);
    for (int i = 6; i >= 0; i--) son7[i] = i - fark >= 0 ? son7[i - fark] : 0;
    sayBugun = 0; havaGunMs = 0;
  }
  gunNo = b; sayacKaydet();
}
void sayacTamam() { sayBugun++; sayToplam++; son7[0] = min<uint32_t>(sayBugun, 65535); sayacKaydet(); }

// ---------------- TEST LOG (RAM halka tampon, /log) ----------------
const int LOG_N = 300; char logSatir[LOG_N][48]; int logBas = 0, logAdet = 0;
void logYaz(const char *fmt, ...) {
  char t[48]; va_list a; va_start(a, fmt); vsnprintf(t, sizeof t, fmt, a); va_end(a);
  Serial.println(t);
  strncpy(logSatir[(logBas + logAdet) % LOG_N], t, 47);
  if (logAdet < LOG_N) logAdet++; else logBas = (logBas + 1) % LOG_N;
}

// ---------------- PARAMETRELER (Preferences) ----------------
struct Param { const char *ad; float *f; uint32_t *u; float mn, mx; };
Param prm[] = {
  {"PULS_ILK_MS", nullptr, &PULS_ILK_MS, 300, 5000}, {"PULS_MIN_MS", nullptr, &PULS_MIN_MS, 100, 2000},
  {"PULS_MAX_MS", nullptr, &PULS_MAX_MS, 1000, 20000}, {"OTURMA_MS", nullptr, &OTURMA_MS, 300, 3000},
  {"ADAPTIF_KATSAYI", &ADAPTIF_KATSAYI, nullptr, 0.3f, 1.5f}, {"BITIS_PSI", &BITIS_PSI, nullptr, 0.1f, 2.0f}};
const char *prmKey(int i) { static const char *k[] = {"pIlk", "pMin", "pMax", "pOtur", "pKat", "pBit"}; return k[i]; }
void paramYukle() {
  for (int i = 0; i < 6; i++) {
    if (prm[i].u) *prm[i].u = constrain(ayar.getUInt(prmKey(i), *prm[i].u), (uint32_t)prm[i].mn, (uint32_t)prm[i].mx);
    else *prm[i].f = constrain(ayar.getFloat(prmKey(i), *prm[i].f), prm[i].mn, prm[i].mx);
  }
  if (PULS_MAX_MS < PULS_MIN_MS) PULS_MAX_MS = PULS_MIN_MS;
}


// ---------------- KALİBRASYON ----------------
// Ortalama ham (kalibrasyonsuz) bar
bool hamOrtalama(float &h) {
  float t = 0; int n = 0; for (int i = 0; i < 20; i++) { float b; if (basincOku(b)) { t += sonHamBar; n++; } delay(2); }
  if (n < 10) return false; h = t / n; return true;
}
bool kalSifir(char *m) {
  float h; if (!hamOrtalama(h)) { strcpy(m, "sensor hatasi"); return false; }
  if (h > 1.0f) { strcpy(m, "basinc var, hortumu bosalt (ham>1 bar)"); return false; }
  sifirOfset = h; ayar.putFloat("ofset", h); bipEkle(2, 60, 60); return true;
}
bool kalKAyar(float k, char *m) {
  if (k < 0.8f || k > 1.2f) { strcpy(m, "kalK sinir 0.8-1.2"); return false; }
  kalK = k; ayar.putFloat("kalK", k); bipEkle(2, 60, 60); return true;
}
bool kalGercek(float gercek, char *m) {
  float h; if (!hamOrtalama(h)) { strcpy(m, "sensor hatasi"); return false; }
  float net = h - sifirOfset;
  if (gercek < 0.5f || net < 0.3f) { strcpy(m, "en az 0.5 bar basincta yap"); return false; }
  return kalKAyar(gercek / net, m);
}
void kalSifirla() { kalK = 1.0f; sifirOfset = 0; ayar.putFloat("kalK", 1.0f); ayar.putFloat("ofset", 0.0f); }

// ---------------- WiFi / OTA / WEB ----------------
void hata(const char *m); void durumSec(Durum d); void baslat(bool test);
extern volatile uint8_t webArt, webAz, webBas, webUzun;
DNSServer dns; WebServer web(80);
bool otaAktif = false;
// Ekranda küçük WiFi ikonu + IP (imzanın solunda). Durum: 0 yok(gri) 1 bağlı(camgöbeği) 2 AP(turuncu)
void wifiCiz() {
  static char onceki[32] = ""; char t[32]; uint8_t d;
  uint8_t n = WiFi.softAPgetStationNum(); d = n ? 1 : 2;
  if (n) snprintf(t, sizeof t, "%s  %u", AP_ADI, n); else snprintf(t, sizeof t, "%s", AP_ADI);
  char k[36]; snprintf(k, sizeof k, "%u%s", d, t); if (!strcmp(k, onceki)) return; strcpy(onceki, k);
  uint16_t r = d == 1 ? C_CYAN : d == 2 ? C_TURUNCU : C_GRI;
  spWifi.fillSprite(C_ARKA);
  for (int i = 0; i < 3; i++) spWifi.drawArc(7, 14, 4 + i * 4, 3 + i * 4, 225, 315, r);   // WiFi yayları
  spWifi.fillCircle(7, 14, 1, r);
  spWifi.loadFont(f_etiket); spWifi.setTextDatum(middle_left); spWifi.setTextColor(r);
  spWifi.drawString(t, 17, 10); spWifi.unloadFont(); spWifi.pushSprite(6, 294);
}
bool calisiyorMu() { return durum == SISIR || durum == OTUR || durum == BOSALT; }
void guncellemeBasla() {   // güvenlik: valf hemen kapanır, işlem durdurulur
  valfKapat(); if (calisiyorMu()) durumSec(BEKLE); testMod = false; otaAktif = true; bipSustur();
}
void ilerlemeCiz(unsigned p) {
  static int son = -1; if ((int)p == son) return; son = p;
  char t[24]; snprintf(t, sizeof t, "GÜNCELLENİYOR %%%u", p);
  spDurum.fillSprite(C_ARKA); spDurum.fillSmoothRoundRect(0, 0, DW, DH, 12, RGB(40,50,70));
  spDurum.fillSmoothRoundRect(0, 0, max(24, (int)(DW * p / 100)), DH, 12, RGB(0,150,200));
  spDurum.loadFont(f_kalin); spDurum.setTextDatum(top_center); spDurum.setTextColor(C_BEYAZ);
  spDurum.drawString(t, DW / 2, 7); spDurum.unloadFont(); spDurum.pushSprite(DX, DY);
}
const char *durumAd() {
  switch (durum) { case SISIR: case OTUR: return "SISIRILIYOR"; case BOSALT: return "BOSALTILIYOR";
    case BITTI: return "TAMAM"; case HATA: return "HATA"; default: return "HAZIR"; }
}
// Panel uclari: cihaz kendi sifreli AP'sini yayinliyor, aga baglanabilen paneli kullanir (ek anahtar yok).
bool yetki() { return true; }
void webJson(bool, const char *fmt, ...) { char j[384]; va_list a; va_start(a, fmt); vsnprintf(j, sizeof j, fmt, a); va_end(a); web.send(200, "application/json; charset=utf-8", j); }
void webHata(const char *m) { bipEkle(1, 300, 50); webJson(false, "{\"ok\":false,\"hata\":\"%s\"}", m); }
void wifiBaslat() {
  setenv("TZ", "<+03>-3", 1); tzset();
  WiFi.persistent(false); WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192,168,4,1), IPAddress(192,168,4,1), IPAddress(255,255,255,0));
  WiFi.softAP(AP_ADI, AP_SIFRE, 6, 0, 4);   // kanal 6, görünür, en çok 4 cihaz
  WiFi.setSleep(false); WiFi.setTxPower(WIFI_POWER_15dBm);
  dns.setErrorReplyCode(DNSReplyCode::NoError); dns.start(53, "*", IPAddress(192,168,4,1));
  ArduinoOTA.setHostname(HOST_ADI);
  ArduinoOTA.onStart([]() { guncellemeBasla(); ilerlemeCiz(0); });
  ArduinoOTA.onProgress([](unsigned a, unsigned t) { valfKapat(); ilerlemeCiz(a * 100 / t); });
  ArduinoOTA.onEnd([]() { ilerlemeCiz(100); });
  ArduinoOTA.onError([](ota_error_t e) { otaAktif = false; hata("GÜNCELLEME HATASI"); });
  web.on("/", []() { web.sendHeader("Content-Encoding", "gzip"); web.sendHeader("Cache-Control", "no-cache");
    web.send_P(200, "text/html; charset=utf-8", (const char *)PANEL_GZ, PANEL_GZ_LEN); });
  // Saat: panel açılınca telefonun saati gelir (internet/NTP yok). Zararsız, anahtarsız.
  web.on("/saat", []() {
    long long e = atoll(web.arg("t").c_str());
    if (e > 1700000000LL && e < 4102444800LL) { timeval tv{(time_t)e, 0}; settimeofday(&tv, nullptr); gunKontrol(); }
    webJson(true, "{\"ok\":true,\"saat\":%s}", saatVar() ? "true" : "false"); });
  // Captive portal: bağlantı kontrollerini panele yönlendir
  static const char *cp[] = {"/generate_204", "/gen_204", "/hotspot-detect.html", "/connecttest.txt", "/ncsi.txt", "/fwlink", "/redirect", "/canonical.html", "/success.txt"};
  auto yon = []() { web.sendHeader("Location", "http://192.168.4.1/"); web.send(302, "text/plain", ""); };
  for (auto u : cp) web.on(u, yon);
  web.onNotFound(yon);
  web.on("/api", []() {
    char j[512]; char s7[64]; snprintf(s7, sizeof s7, "[%u,%u,%u,%u,%u,%u,%u]", son7[0], son7[1], son7[2], son7[3], son7[4], son7[5], son7[6]);
    snprintf(j, sizeof j, "{\"basinc_bar\":%.3f,\"hedef_bar\":%.3f,\"birim\":\"%s\",\"durum\":\"%s\",\"hata\":\"%s\",\"sensor\":%s,\"test\":%s,"
      "\"bugun\":%lu,\"toplam\":%lu,\"hava_gun_s\":%lu,\"hava_top_s\":%lu,\"son7\":%s,\"saat\":%s,\"ham_mv\":%.0f,\"ham_bar\":%.3f,\"kalK\":%.4f,\"ofset\":%.4f,\"puls\":%u}",
      basinc, hedefBar, birimAd(), durumAd(), durum == HATA ? hataMsj : "", sensorOk ? "true" : "false", testMod ? "true" : "false",
      (unsigned long)sayBugun, (unsigned long)sayToplam, (unsigned long)(havaGunMs / 1000), (unsigned long)(havaTopMs / 1000), s7,
      saatVar() ? "true" : "false", sonHamMv, sonHamBar, kalK, sifirOfset, pulsNo);
    web.send(200, "application/json; charset=utf-8", j); });
  web.on("/ham", []() { webJson(true, "{\"ham_mv\":%.0f,\"ham_bar\":%.4f,\"bar_filtresiz\":%.3f,\"bar_filtreli\":%.3f,\"sensor\":%s}",
    sonHamMv, sonHamBar, max(0.0f, (sonHamBar - sifirOfset) * kalK), basinc, sensorOk ? "true" : "false"); });
  web.on("/kal", []() {
    if (!yetki()) return;
    if (calisiyorMu()) { webHata("calisirken kalibrasyon yapilamaz"); return; }
    char m[64];
    if (web.hasArg("sifirla")) { kalSifirla(); bipEkle(1, 60, 40); }
    else if (web.hasArg("sifir")) { if (!kalSifir(m)) { webHata(m); return; } }
    else if (web.hasArg("gercek")) { if (!kalGercek(web.arg("gercek").toFloat(), m)) { webHata(m); return; } }
    else if (web.hasArg("kat")) { if (!kalKAyar(web.arg("kat").toFloat(), m)) { webHata(m); return; } }   // /kal?kat=1.03
    webJson(true, "{\"ok\":true,\"kalK\":%.4f,\"ofset\":%.4f}", kalK, sifirOfset); });
  web.on("/test", []() {
    if (!yetki()) return;
    if (web.hasArg("dur")) { valfKapat(); if (calisiyorMu()) durumSec(BEKLE); testMod = false; logYaz("# DURDURULDU (web)"); bipEkle(1, 60, 40); webJson(true, "{\"ok\":true,\"durum\":\"%s\"}", durumAd()); return; }
    if (web.hasArg("baslat")) {
      if (calisiyorMu()) { webHata("zaten calisiyor"); return; }
      if (otaAktif) { webHata("guncelleme var"); return; }
      if (!sensorOk) { hata("SENSÖR HATASI"); webHata("sensor hatasi"); return; }
      if (web.hasArg("hedef")) TEST_HEDEF_PSI = constrain(web.arg("hedef").toFloat(), 5.0f, 60.0f);
      if (web.hasArg("puls")) TEST_PULS_MS = constrain((uint32_t)web.arg("puls").toInt(), 300UL, 6000UL);
      sesBasla(); baslat(true);
      webJson(true, "{\"ok\":true,\"hedef_psi\":%.1f,\"puls_ms\":%lu}", TEST_HEDEF_PSI, (unsigned long)TEST_PULS_MS); return; }
    webJson(true, "{\"durum\":\"%s\",\"test\":%s,\"puls\":%u,\"hedef_psi\":%.1f,\"puls_ms\":%lu}", durumAd(), testMod ? "true" : "false", pulsNo, TEST_HEDEF_PSI, (unsigned long)TEST_PULS_MS); });
  web.on("/tus", []() {   // telefon butonları
    String b = web.arg("b");
    if (b == "art") { if (webArt < 20) webArt++; } else if (b == "az") { if (webAz < 20) webAz++; }
    else if (b == "bas") webBas = 1; else if (b == "birim") webUzun = 1;
    else { webHata("buton?"); return; }
    webJson(true, "{\"ok\":true}"); });
  web.on("/param", []() {
    bool degisti = false;
    for (int i = 0; i < 6; i++) if (web.hasArg(prm[i].ad)) {
      if (!degisti && !yetki()) return;
      if (calisiyorMu()) { webHata("calisirken degistirilemez"); return; }
      float v = web.arg(prm[i].ad).toFloat();
      if (v < prm[i].mn || v > prm[i].mx) { char m[64]; snprintf(m, sizeof m, "%s sinir %g-%g", prm[i].ad, prm[i].mn, prm[i].mx); webHata(m); return; }
      if (prm[i].u) { *prm[i].u = (uint32_t)v; ayar.putUInt(prmKey(i), *prm[i].u); } else { *prm[i].f = v; ayar.putFloat(prmKey(i), v); }
      degisti = true;
    }
    if (PULS_MAX_MS < PULS_MIN_MS) { PULS_MAX_MS = PULS_MIN_MS; ayar.putUInt("pMax", PULS_MAX_MS); }
    if (degisti) bipEkle(1, 60, 40);
    String j = "{"; for (int i = 0; i < 6; i++) { j += "\""; j += prm[i].ad; j += "\":"; j += prm[i].u ? String(*prm[i].u) : String(*prm[i].f, 3);
      j += ",\""; j += prm[i].ad; j += "_sinir\":["; j += String(prm[i].mn, 2); j += ","; j += String(prm[i].mx, 2); j += "]"; if (i < 5) j += ","; }
    j += "}"; web.send(200, "application/json", j); });
  web.on("/ayar", []() {   // hedef (bar) ve birim (bar/psi/kpa)
    if (!yetki()) return;
    if (calisiyorMu()) { webHata("calisirken degistirilemez"); return; }
    if (web.hasArg("hedef")) { hedefBar = constrain(web.arg("hedef").toFloat(), HEDEF_MIN_BAR, HEDEF_MAX_BAR); ayar.putFloat("hedef", hedefBar); }
    if (web.hasArg("birim")) { String b = web.arg("birim"); b.toLowerCase(); birim = b == "psi" ? PSI : b == "kpa" ? KPA : BAR; ayar.putUChar("birim", birim); }
    if (durum == BITTI || durum == HATA) { durum = BEKLE; testMod = false; }
    bipEkle(1, 60, 40);
    webJson(true, "{\"ok\":true,\"hedef_bar\":%.3f,\"birim\":\"%s\"}", hedefBar, birimAd()); });
  web.on("/log", []() {
    String t; t.reserve(logAdet * 40 + 64);
    for (int i = 0; i < logAdet; i++) { t += logSatir[(logBas + i) % LOG_N]; t += '\n'; }
    web.send(200, "text/plain; charset=utf-8", t); });
  web.on("/update", HTTP_GET, []() {
    web.send(200, "text/html; charset=utf-8", "<meta name=viewport content='width=device-width'><body style='background:#0b0e14;color:#ddd;font-family:sans-serif'><h3>Lastik Sisirme - Firmware yukle</h3>"
      "<form method=POST action=/update enctype=multipart/form-data>"
      "<input type=file name=f accept=.bin> <input type=submit value=Yukle></form>"); });
  web.on("/update", HTTP_POST, []() {
    web.send(200, "text/plain", Update.hasError() ? "HATA" : "TAMAM, yeniden basliyor"); delay(500); if (!Update.hasError()) ESP.restart(); },
    []() {
      HTTPUpload &u = web.upload();
      if (u.status == UPLOAD_FILE_START) { guncellemeBasla(); ilerlemeCiz(0); Update.begin(UPDATE_SIZE_UNKNOWN); }
      else if (u.status == UPLOAD_FILE_WRITE) { valfKapat(); Update.write(u.buf, u.currentSize); ilerlemeCiz(min(99u, (unsigned)(Update.progress() * 100 / max(1u, (unsigned)web.header("Content-Length").toInt())))); }
      else if (u.status == UPLOAD_FILE_END) { if (Update.end(true)) ilerlemeCiz(100); else { otaAktif = false; hata("GÜNCELLEME HATASI"); } }
    });
  const char *hdr[] = {"Content-Length"}; web.collectHeaders(hdr, 1);
}
// loop içinde: kısa, bloklamayan işler
void wifiIsle() {
  static bool servis = false;
  if (!servis) { ArduinoOTA.begin(); web.begin(); servis = true; }
  dns.processNextRequest(); web.handleClient(); ArduinoOTA.handle();
  static uint32_t t = 0; if (millis() - t > 1000) { t = millis(); wifiCiz(); }
}

// ---------------- BUTONLAR ----------------
// Basit debounce; tekrar (basılı tutunca hızlı artış) ve uzun basış desteği.
struct Buton { int pin; bool bas; uint32_t t, tekrar; bool uzunOldu; };
Buton bArt{PIN_BTN_ART}, bAz{PIN_BTN_AZ}, bBas{PIN_BTN_BAS};
// Telefondan sanal butonlar (/tus?b=art|az|bas|birim): fiziksel butonla aynı işi yapar
volatile uint8_t webArt = 0, webAz = 0, webBas = 0, webUzun = 0;
// 0: olay yok, 1: kısa/tekrar, 2: uzun
int butonOku(Buton &b, bool tekrarli) {
  bool simdi = digitalRead(b.pin) == LOW; uint32_t n = millis();
  if (simdi && !b.bas) { sesTik(); b.bas = true; b.t = n; b.tekrar = n + 500; b.uzunOldu = false; return tekrarli ? 1 : 0; }
  if (simdi && b.bas) {
    if (tekrarli && n >= b.tekrar) { b.tekrar = n + 120; sesTik(); return 1; }
    if (!tekrarli && !b.uzunOldu && n - b.t > 1000) { b.uzunOldu = true; return 2; }
  }
  if (!simdi && b.bas) { b.bas = false; if (!tekrarli && !b.uzunOldu && n - b.t > 40) return 1; }
  return 0;
}

void hata(const char *m) { valfKapat(); if (durum != HATA || hataMsj != m) sesHata(); durum = HATA; hataMsj = m; durumT = millis(); }
float otOnceki = -100; uint32_t otSonT = 0;   // OTUR: basınç oturdu mu kontrolü
void durumSec(Durum d) { if (d == BITTI && durum != BITTI) { sesTamam(); havaSay(); if (!testMod) sayacTamam(); } if (d == OTUR) otOnceki = -100; durum = d; durumT = millis(); }
void hataBitir(const char *m) { hata(m); bitisMs = millis() - basT; }
// Oturmadan sonra birkaç okumanın ortalaması (bar)
bool olc(float &bar) {
  float top = 0; int n = 0;
  for (int i = 0; i < OLCUM_ORNEK; i++) { float b; if (basincOku(b)) { top += b; n++; } delay(5); }
  if (n < OLCUM_ORNEK / 2) return false;
  bar = top / n; return true;
}
void baslat(bool test) {
  testMod = test; basT = millis(); yukselmez = 0; pulsNo = 0; pulsSure = test ? TEST_PULS_MS : PULS_ILK_MS;
  pulsOncesi = -1; bitisMs = 0; durumSec(OTUR);
  if (test) { logYaz("# TEST hedef_psi=%.1f puls_ms=%lu", TEST_HEDEF_PSI, (unsigned long)TEST_PULS_MS); logYaz("zaman_ms,puls_no,puls_ms,basinc_psi,artis_psi,psi_per_s"); }
}

// ---------------- KURULUM ----------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_VALF_SIS, OUTPUT); digitalWrite(PIN_VALF_SIS, LOW);
  pinMode(PIN_VALF_BOS, OUTPUT); digitalWrite(PIN_VALF_BOS, LOW);
  pinMode(PIN_BTN_ART, INPUT_PULLUP); pinMode(PIN_BTN_AZ, INPUT_PULLUP); pinMode(PIN_BTN_BAS, INPUT_PULLUP);
  analogReadResolution(12); analogSetPinAttenuation(PIN_SENSOR, ADC_11db);
  ledcAttach(PIN_BUZZER, 2700, 8); ledcWriteTone(PIN_BUZZER, 0);
  ekranBaslat();
  ayar.begin("sisirme", false);
  hedefBar = ayar.getFloat("hedef", 2.2f); birim = ayar.getUChar("birim", BAR);
  // Açılışta hortum boşken sıfır kalibrasyonu: +/− birlikte basılı açılırsa ofset kaydedilir
  float b;
  if (digitalRead(PIN_BTN_ART) == LOW && digitalRead(PIN_BTN_AZ) == LOW && basincOku(b)) {
    ayar.putFloat("ofset", sonHamBar); mesaj("SIFIR KAYDEDİLDİ", C_YESIL); bipEkle(2, 70, 70); { uint32_t t0 = millis(); while (millis() - t0 < 1500) { bipIsle(); delay(5); } }
  }
  sifirOfset = ayar.getFloat("ofset", 0.0f);
  kalK = constrain(ayar.getFloat("kalK", 1.0f), 0.8f, 1.2f);
  paramYukle(); sayacYukle(); ogrRate = constrain(ayar.getFloat("oRate", 1.92f), 0.2f, 20.0f); ogrVar = ayar.isKey("oRate");
  // TEST MODU: açılışta BAŞLAT basılı tutulursa
  if (digitalRead(PIN_BTN_BAS) == LOW) {
    mesaj("TEST MODU", RGB(150,50,200)); bipEkle(1, 120, 60); { uint32_t t0 = millis(); while (millis() - t0 < 1500) { bipIsle(); delay(5); } }
    while (digitalRead(PIN_BTN_BAS) == LOW) delay(10);   // bırakınca başla (kısa basış sayılmasın)
    bBas.bas = false;
    if (basincOku(b)) baslat(true); else hata("SENSÖR HATASI");
  }
  wifiBaslat();
}

// ---------------- ANA DÖNGÜ ----------------
void loop() {
  static uint32_t sonOkuma = 0;
  if (millis() - sonOkuma >= 50) {
    sonOkuma = millis();
    float b; sensorOk = basincOku(b);
    // Güçlü filtre: yavaş değişimde sakin, hızlı değişimde (şişirme) çabuk takip eder
    // Vana açıkken / oturma sırasında sensör kompresör hattını görür (lastiği değil):
    // ekrandaki değer son ölçülen lastik basıncında kalır. Sadece sensör sınırına yakın değerde dur.
    bool hatAcik = durum == SISIR || durum == OTUR || durum == BOSALT;
    if (sensorOk && hatAcik) { if (b > 12.5f) hataBitir("AŞIRI BASINÇ!"); }
    else if (sensorOk) {
      float fark = fabsf(b - basinc);
      float k = fark > 0.15f ? 0.5f : 0.08f;
      basinc += (b - basinc) * k;
    }
  }
  // Mutlak güvenlik
  if (sensorOk && basinc > MUTLAK_MAX_BAR) { if (durum != HATA) bitisMs = millis() - basT; hata("AŞIRI BASINÇ!"); }
  if (!sensorOk && (durum == SISIR || durum == OTUR || durum == BOSALT)) hataBitir("SENSÖR HATASI");

  // Serial'dan "TEST" -> test modu
  static String gelen;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { gelen.trim(); gelen.toUpperCase();
      if (gelen == "TEST" && !(durum == SISIR || durum == OTUR || durum == BOSALT)) { if (sensorOk) baslat(true); else hata("SENSÖR HATASI"); }
      else if (gelen.startsWith("KAL") && (durum == SISIR || durum == OTUR || durum == BOSALT)) Serial.println("HATA calisirken kalibrasyon yapilamaz");
      else if (gelen.startsWith("KAL")) {   // KAL SIFIR | KAL GERCEK 2.20 | KAL K 1.03 | KAL SIFIRLA
        char m[64] = "ok"; bool ok = true;
        if (gelen == "KAL SIFIRLA") kalSifirla();
        else if (gelen == "KAL SIFIR") ok = kalSifir(m);
        else if (gelen.startsWith("KAL GERCEK ")) ok = kalGercek(gelen.substring(11).toFloat(), m);
        else if (gelen.startsWith("KAL K ")) ok = kalKAyar(gelen.substring(6).toFloat(), m);
        Serial.printf("%s %s kalK=%.4f ofset=%.4f\n", ok ? "OK" : "HATA", m, kalK, sifirOfset);
      }
      gelen = ""; }
    else if (gelen.length() < 32) gelen += c;
  }
  int art = butonOku(bArt, true), az = butonOku(bAz, true), bas = butonOku(bBas, false);
  if (webArt) { webArt--; art = 1; sesTik(); }
  else if (webAz) { webAz--; az = 1; sesTik(); }
  if (webBas) { webBas = 0; bas = 1; sesTik(); }
  else if (webUzun) { webUzun = 0; bas = 2; }
  bool calisiyor = durum == SISIR || durum == OTUR || durum == BOSALT;

  if (!calisiyor && (art || az)) {
    // Adım seçili birimde: psi 0,1 / bar 0,05 / kPa 5. Yuvarlama da o birimde, sonra bar'a çevrilir.
    float adim = birim == PSI ? 0.1f : birim == KPA ? 5.0f : 0.05f;
    float carpan = birim == PSI ? PSI_BAR : birim == KPA ? 100.0f : 1.0f;
    float v = roundf(hedefBar * carpan / adim) + (art ? 1 : -1);
    float minA = ceilf(HEDEF_MIN_BAR * carpan / adim - 0.001f), maxA = floorf(HEDEF_MAX_BAR * carpan / adim + 0.001f);
    v = constrain(v, minA, maxA);
    hedefBar = v * adim / carpan;
    ayar.putFloat("hedef", hedefBar);
    if (durum == BITTI || durum == HATA) { durum = BEKLE; testMod = false; }
  }
  if (bas == 2 && !calisiyor) { sesBirim(); birim = (birim + 1) % 3; ayar.putUChar("birim", birim); }
  if (bas == 1) {
    if (calisiyor) { valfKapat(); durumSec(BEKLE); testMod = false; }
    else if (!sensorOk) hata("SENSÖR HATASI");
    else if (basinc < LASTIK_MIN_BAR && !lastikUyari()) { lastikUyariT = millis(); bipEkle(1, 60, 40); }   // 3 sn içinde tekrar basınca başlar
    else { lastikUyariT = 0; sesBasla(); baslat(false); }
  }

  uint32_t gecen = millis() - durumT;
  if (calisiyor && millis() - basT > TOPLAM_MAX_MS) hataBitir("ZAMAN AŞIMI");

  switch (durum) {
    case OTUR: {  // valf kapalı, basınç oturdu mu? -> ortalama ölç, karar ver
      if (gecen < (testMod ? TEST_OTURMA_MS : OTURMA_MS)) break;
      float m;
      if (!olc(m)) { hataBitir("SENSÖR HATASI"); break; }
      // Hortum/T içindeki basınç lastikle dengelenene kadar bekle: 250 ms arayla iki ölçüm
      // 0,3 psi'den az farklıysa (oturmaya başladı) ölç (en fazla 2,5 sn). Böylece puls sonrası
      // hattaki geçici yüksek basınç "hedefe ulaştı" sanılıp erken durmaz.
      if (millis() - otSonT < 250 && otOnceki > -50) break;
      if (gecen < 2500 && (otOnceki < -50 || fabsf(m - otOnceki) * PSI_BAR > 0.3f)) { otOnceki = m; otSonT = millis(); break; }
      basinc = m;
      if (m > MUTLAK_MAX_BAR) { hataBitir("AŞIRI BASINÇ!"); break; }   // vana kapalı, oturmuş ölçüm
      float hedef = testMod ? TEST_HEDEF_PSI / PSI_BAR : hedefBar;
      float kalanPsi = (hedef - m) * PSI_BAR;
      float artis = 0, rate = 0;
      if (pulsOncesi >= 0) { artis = (m - pulsOncesi) * PSI_BAR; rate = artis / (pulsSure / 1000.0f); }
      if (testMod && pulsNo > 0) {
        logYaz("%lu,%u,%lu,%.2f,%.2f,%.3f", (unsigned long)(millis() - basT), pulsNo, (unsigned long)pulsSure, m * PSI_BAR, artis, rate);
      }
      if (kalanPsi <= BITIS_PSI) {
        valfKapat(); bitisMs = millis() - basT;
        if (testMod) logYaz("# BITTI toplam_ms=%lu puls=%u", (unsigned long)bitisMs, pulsNo);
        if (kalanPsi < -FAZLA_BAR * PSI_BAR && TAHLIYE_VALFI && !testMod) {
          pulsSure = constrain((uint32_t)(-kalanPsi / PSI_BAR * 2000), (uint32_t)PULS_MIN_MS, 1500UL); pulsOncesi = -1; bosaltAc(); durumSec(BOSALT);
        } else durumSec(BITTI);   // tek valf: fazlaysa ekran "FAZLA" uyarısı verir, elle boşaltılır
        break;
      }
      // Artış yoksa say (kompresör boş / kaçak)
      if (pulsOncesi >= 0 && artis < ARTIS_ESIK_PSI) {
        if (++yukselmez >= ARTISSIZ_MAX) { hataBitir("HAVA YOK / KAÇAK"); if (testMod) logYaz("# HATA HAVA YOK / KACAK"); break; }
      } else yukselmez = 0;
      // Ölçülen hızı öğren (kısa pulslar gürültülü, sayma)
      if (!testMod && pulsOncesi >= 0 && pulsSure >= 800 && rate > 0.2f) {
        ogrRate = constrain(ogrRate * 0.5f + rate * 0.5f, 0.2f, 20.0f); ayar.putFloat("oRate", ogrRate); ogrVar = true;
      }
      // Hız tahmini: bu lastikte ölçülen + öğrenilen ortalaması
      float hiz = (pulsOncesi >= 0 && rate > 0.001f) ? rate * 0.5f + ogrRate * 0.5f : ogrRate;
      bool ince = kalanPsi <= YAKLASMA_PSI;   // hedefe 7 psi kala (32 hedefte 25 psi) ince bölge
      if (testMod) pulsSure = TEST_PULS_MS;
      else if (pulsOncesi >= 0 && rate <= 0.001f) pulsSure = constrain(pulsSure * 2, (uint32_t)PULS_MIN_MS, ince ? (uint32_t)INCE_MAX_MS : (uint32_t)PULS_MAX_MS);   // artış yok: uzat
      else if (!ince && pulsOncesi < 0)       // ilk puls, lastik düşük: basınca göre uzun ama ~25 psi'yi hedefler (aşmasın)
        pulsSure = constrain((uint32_t)(min(kalanPsi * ILK_KATSAYI, kalanPsi - YAKLASMA_PSI + 1.0f) / hiz * 1000.0f), (uint32_t)PULS_MIN_MS, (uint32_t)PULS_MAX_MS);
      else if (!ince)                         // yaklaşma: 25 psi civarına kadar tek seferde
        pulsSure = constrain((uint32_t)((kalanPsi - YAKLASMA_PSI + 1.0f) / hiz * 1000.0f), (uint32_t)PULS_MIN_MS, (uint32_t)PULS_MAX_MS);
      else                                    // ince: kalanın yarısı kadar, kısa ve sık
        pulsSure = constrain((uint32_t)(kalanPsi / hiz * 0.5f * 1000.0f), (uint32_t)PULS_MIN_MS, (uint32_t)INCE_MAX_MS);
      pulsOncesi = m; pulsNo++; sisirAc(); durumSec(SISIR);
      break; }
    case SISIR:
      if (gecen >= pulsSure) { valfKapat(); durumSec(OTUR); }
      break;
    case BOSALT:
      if (gecen >= pulsSure) { valfKapat(); pulsOncesi = -1; durumSec(OTUR); }
      break;
    default: break;
  }
  bipIsle();
  wifiIsle();
  { static uint32_t gt = 0; if (millis() - gt > 10000) { gt = millis(); gunKontrol(); } }
  if (!otaAktif) ekranCiz();
}
