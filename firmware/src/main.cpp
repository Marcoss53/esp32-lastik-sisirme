/*
 * ESP32 Otomatik Lastik Şişirme İstasyonu
 * Kart    : ESP32 DevKit (ESP-WROOM-32)
 * Valf    : 12V NC solenoid (şimdi 2W-025-08), TIP102 ile sürülür (GPIO25 HIGH = açık)
 *           GPIO25 -> 1K -> B, B -> 10K -> GND, E -> GND, C -> valf(-), valf(+) -> 12V, 1N4007 valfe ters paralel
 * Tahliye : İsteğe bağlı 2. valf GPIO26 (TAHLIYE_VALFI=1 ile açılır, varsayılan kapalı)
 * Sensör  : 0.5-4.5V, 5V beslemeli, 200 PSI (13,79 bar). 10k (üst) + 20k (alt) bölücü -> GPIO34
 * Ekran   : Waveshare 2" ST7789V 240x320 (DIN 23, CLK 18, CS 5, DC 16, RST 17, BL 4)
 * Butonlar: GPIO32 "+", GPIO33 "−", GPIO27 BAŞLAT/DURDUR (uzun bas: birim kPa/bar/psi)
 */
#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <Preferences.h>

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
const int TFT_CS = 5, TFT_DC = 16, TFT_RST = 17, TFT_BL = 4;  // MOSI 23, SCK 18 (donanım SPI)

// ---------------- KALİBRASYON ----------------
const float BOLUCU_ORAN   = 20.0f / 30.0f;  // 20k / (10k + 20k)
const float SENSOR_V_MIN  = 0.5f;           // 0 bar çıkışı (V)
const float SENSOR_V_MAX  = 4.5f;           // tam skala çıkışı (V)
const float SENSOR_BAR_MAX = 13.79f;        // 200 PSI
float sifirOfset = 0.0f;                    // açılışta ölçülen sıfır hatası (bar)

// ---------------- GÜVENLİK / KONTROL ----------------
const float MUTLAK_MAX_BAR = 10.0f;    // aşılırsa valf kapanır, hata
const float HEDEF_MIN_BAR  = 0.5f;
const float HEDEF_MAX_BAR  = 9.0f;
const float ADIM_BAR       = 0.1f;
const float TOLERANS_BAR   = 0.05f;
const float FAZLA_BAR      = 0.15f;    // hedefin bu kadar üstü = aşırı basınç uyarısı
const float SENSOR_KOPUK_V = 0.3f;
const float SENSOR_KISA_V  = 4.8f;
const float LASTIK_YOK_BAR = 0.15f;
const uint32_t OTURMA_MS   = 500;      // puls sonrası ölçüm beklemesi
const uint32_t PULS_MAX_MS = 3000;
const uint32_t PULS_MIN_MS = 100;
const uint32_t TOPLAM_MAX_MS = 5UL * 60UL * 1000UL;
const uint8_t  YUKSELMEZ_MAX = 4;

// ---------------- NESNELER / DURUM ----------------
Adafruit_ST7789 tft(TFT_CS, TFT_DC, TFT_RST);
Preferences ayar;
enum Durum { BEKLE, SISIR, OTUR, BOSALT, BITTI, HATA };
Durum durum = BEKLE;
enum Birim { KPA, BAR, PSI };
uint8_t birim = BAR;
float hedefBar = 2.2f, basinc = 0, pulsOncesi = 0;
bool sensorOk = true;
uint32_t durumT = 0, basT = 0, pulsSure = 800;
uint8_t yukselmez = 0;
const char *hataMsj = "";

// ---------------- VALF ----------------
void valfKapat() { digitalWrite(PIN_VALF_SIS, LOW); if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, LOW); }
void sisirAc()   { if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, LOW); delay(5); digitalWrite(PIN_VALF_SIS, HIGH); }
void bosaltAc()  { digitalWrite(PIN_VALF_SIS, LOW); delay(5); if (TAHLIYE_VALFI) digitalWrite(PIN_VALF_BOS, HIGH); }

// ---------------- SENSÖR ----------------
// 16 örnek ortalaması; analogReadMilliVolts ESP32'nin fabrika ADC kalibrasyonunu kullanır.
bool basincOku(float &bar) {
  uint32_t top = 0;
  for (int i = 0; i < 16; i++) top += analogReadMilliVolts(PIN_SENSOR);
  float v = (top / 16.0f) / 1000.0f / BOLUCU_ORAN;  // gerçek sensör gerilimi
  if (v < SENSOR_KOPUK_V || v > SENSOR_KISA_V) return false;
  bar = (v - SENSOR_V_MIN) * SENSOR_BAR_MAX / (SENSOR_V_MAX - SENSOR_V_MIN) - sifirOfset;
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

// ---------------- EKRAN ----------------
// Yalnız değişince çizer (titreme olmasın diye).
const uint16_t RENK_ARKA = ST77XX_BLACK;
void ortala(const char *s, int y, uint8_t boyut, uint16_t renk) {
  int16_t x1, y1; uint16_t w, h;
  tft.setTextSize(boyut); tft.getTextBounds(s, 0, 0, &x1, &y1, &w, &h);
  tft.setTextColor(renk, RENK_ARKA); tft.setCursor((240 - w) / 2, y); tft.print(s);
}
void ekranCiz() {
  static char onceki[64] = "";
  char a[16], h[16], anah[64];
  yaz(a, basinc); yaz(h, hedefBar);
  snprintf(anah, sizeof anah, "%s|%s|%d|%d|%d", a, h, durum, birim, sensorOk);
  if (!strcmp(anah, onceki)) return;
  strcpy(onceki, anah);
  tft.fillScreen(RENK_ARKA);
  ortala("LASTIK SISIRME", 12, 2, ST77XX_CYAN);
  tft.drawFastHLine(10, 36, 220, 0x4208);
  ortala("BASINC", 52, 2, 0xAD55);
  bool fazla = sensorOk && basinc > hedefBar + FAZLA_BAR;
  ortala(sensorOk ? a : "---", 82, 6, fazla ? ST77XX_RED : ST77XX_WHITE);
  ortala(birimAd(), 136, 2, 0xAD55);
  // hedef kutusu
  tft.drawRoundRect(20, 170, 200, 60, 10, ST77XX_YELLOW);
  ortala("HEDEF", 178, 1, ST77XX_YELLOW);
  char hb[24]; snprintf(hb, sizeof hb, "%s %s", h, birimAd());
  ortala(hb, 196, 3, ST77XX_YELLOW);
  // durum satırı
  const char *d = "HAZIR"; uint16_t r = ST77XX_GREEN;
  switch (durum) {
    case SISIR: case OTUR: d = "SISIRILIYOR"; r = ST77XX_CYAN; break;
    case BOSALT: d = "BOSALTILIYOR"; r = ST77XX_ORANGE; break;
    case BITTI: d = "TAMAM"; r = ST77XX_GREEN; break;
    case HATA: d = hataMsj; r = ST77XX_RED; break;
    default: if (fazla) { d = "FAZLA! HAVA BOSALT"; r = ST77XX_RED; } break;
  }
  if (!sensorOk && durum != HATA) { d = "SENSOR HATASI"; r = ST77XX_RED; }
  tft.fillRoundRect(10, 248, 220, 34, 8, r);
  tft.setTextColor(ST77XX_BLACK, r);
  { int16_t x1, y1; uint16_t w, hh; tft.setTextSize(2); tft.getTextBounds(d, 0, 0, &x1, &y1, &w, &hh); tft.setCursor((240 - w) / 2, 257); tft.print(d); }
  ortala("+/-: hedef  BASLAT: bas/dur", 296, 1, 0x7BEF);
  ortala("BASLAT uzun: birim", 308, 1, 0x7BEF);
}

// ---------------- BUTONLAR ----------------
// Basit debounce; tekrar (basılı tutunca hızlı artış) ve uzun basış desteği.
struct Buton { int pin; bool bas; uint32_t t, tekrar; bool uzunOldu; };
Buton bArt{PIN_BTN_ART}, bAz{PIN_BTN_AZ}, bBas{PIN_BTN_BAS};
// 0: olay yok, 1: kısa/tekrar, 2: uzun
int butonOku(Buton &b, bool tekrarli) {
  bool simdi = digitalRead(b.pin) == LOW; uint32_t n = millis();
  if (simdi && !b.bas) { b.bas = true; b.t = n; b.tekrar = n + 500; b.uzunOldu = false; return tekrarli ? 1 : 0; }
  if (simdi && b.bas) {
    if (tekrarli && n >= b.tekrar) { b.tekrar = n + 120; return 1; }
    if (!tekrarli && !b.uzunOldu && n - b.t > 1000) { b.uzunOldu = true; return 2; }
  }
  if (!simdi && b.bas) { b.bas = false; if (!tekrarli && !b.uzunOldu && n - b.t > 40) return 1; }
  return 0;
}

void hata(const char *m) { valfKapat(); durum = HATA; hataMsj = m; durumT = millis(); }
void durumSec(Durum d) { durum = d; durumT = millis(); }

// ---------------- KURULUM ----------------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_VALF_SIS, OUTPUT); digitalWrite(PIN_VALF_SIS, LOW);
  pinMode(PIN_VALF_BOS, OUTPUT); digitalWrite(PIN_VALF_BOS, LOW);
  pinMode(PIN_BTN_ART, INPUT_PULLUP); pinMode(PIN_BTN_AZ, INPUT_PULLUP); pinMode(PIN_BTN_BAS, INPUT_PULLUP);
  analogReadResolution(12); analogSetPinAttenuation(PIN_SENSOR, ADC_11db);
  pinMode(TFT_BL, OUTPUT); digitalWrite(TFT_BL, HIGH);
  tft.init(240, 320); tft.setRotation(0); tft.fillScreen(RENK_ARKA);
  ayar.begin("sisirme", false);
  hedefBar = ayar.getFloat("hedef", 2.2f); birim = ayar.getUChar("birim", BAR);
  // Açılışta hortum boşken sıfır kalibrasyonu: +/− birlikte basılı açılırsa ofset kaydedilir
  float b;
  if (digitalRead(PIN_BTN_ART) == LOW && digitalRead(PIN_BTN_AZ) == LOW && basincOku(b)) {
    ayar.putFloat("ofset", b); ortala("SIFIR KAYDEDILDI", 150, 2, ST77XX_GREEN); delay(1500);
  }
  sifirOfset = ayar.getFloat("ofset", 0.0f);
}

// ---------------- ANA DÖNGÜ ----------------
void loop() {
  static uint32_t sonOkuma = 0;
  if (millis() - sonOkuma >= 50) {
    sonOkuma = millis();
    float b; sensorOk = basincOku(b);
    if (sensorOk) basinc = basinc * 0.6f + b * 0.4f;   // hafif filtre
  }
  // Mutlak güvenlik
  if (sensorOk && basinc > MUTLAK_MAX_BAR) hata("ASIRI BASINC!");
  if (!sensorOk && (durum == SISIR || durum == OTUR || durum == BOSALT)) hata("SENSOR HATASI");

  int art = butonOku(bArt, true), az = butonOku(bAz, true), bas = butonOku(bBas, false);
  bool calisiyor = durum == SISIR || durum == OTUR || durum == BOSALT;

  if (!calisiyor && (art || az)) {
    hedefBar += art ? ADIM_BAR : -ADIM_BAR;
    hedefBar = constrain(roundf(hedefBar * 10) / 10.0f, HEDEF_MIN_BAR, HEDEF_MAX_BAR);
    ayar.putFloat("hedef", hedefBar);
    if (durum == BITTI || durum == HATA) durum = BEKLE;
  }
  if (bas == 2 && !calisiyor) { birim = (birim + 1) % 3; ayar.putUChar("birim", birim); }
  if (bas == 1) {
    if (calisiyor) { valfKapat(); durumSec(BEKLE); }
    else if (!sensorOk) hata("SENSOR HATASI");
    else if (basinc < LASTIK_YOK_BAR) hata("LASTIK TAKILI DEGIL");
    else { basT = millis(); yukselmez = 0; pulsSure = 800; durumSec(OTUR); }
  }

  uint32_t gecen = millis() - durumT;
  if (calisiyor && millis() - basT > TOPLAM_MAX_MS) hata("ZAMAN ASIMI");

  switch (durum) {
    case OTUR:   // valf kapalı, basınç oturdu mu? -> ölç, karar ver
      if (gecen < OTURMA_MS) break;
      {
        float fark = hedefBar - basinc;
        if (fabsf(fark) <= TOLERANS_BAR) { valfKapat(); durumSec(BITTI); break; }
        if (fark < 0) {
          if (TAHLIYE_VALFI && -fark > TOLERANS_BAR) { pulsSure = constrain((uint32_t)(-fark * 2000), PULS_MIN_MS, 1500UL); bosaltAc(); durumSec(BOSALT); }
          else { valfKapat(); durumSec(BEKLE); }   // tek valf: ekran "FAZLA" uyarısı verir, elle boşaltılır
          break;
        }
        // Basınç yükselmiyorsa (kompresör boş / kaçak) say
        if (pulsOncesi > 0 && basinc - pulsOncesi < 0.01f) { if (++yukselmez >= YUKSELMEZ_MAX) { hata("BASINC ARTMIYOR"); break; } }
        else yukselmez = 0;
        // Hedefe yaklaştıkça puls kısalır (1 bar fark ~ 3 sn)
        pulsSure = constrain((uint32_t)(fark * 3000), PULS_MIN_MS, PULS_MAX_MS);
        pulsOncesi = basinc; sisirAc(); durumSec(SISIR);
      }
      break;
    case SISIR:
      if (gecen >= pulsSure) { valfKapat(); durumSec(OTUR); }
      break;
    case BOSALT:
      if (gecen >= pulsSure) { valfKapat(); pulsOncesi = 0; durumSec(OTUR); }
      break;
    default: break;
  }
  ekranCiz();
}
