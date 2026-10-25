# ESP32 Tire Inflator / ESP32 Otomatik Lastik Şişirme İstasyonu

![Front](enclosure/renders/on.png)

[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english)

---

## Türkçe

### Genel bakış
Kompresör hattına takılan, hedef basınca kadar lastiği otomatik şişiren ESP32 istasyonu. Hedefi butonlarla ayarlarsın, BAŞLAT'a basınca 12V NC solenoid valf kısa pulslarla açılır; her pulstan sonra basınç oturur ve ölçülür, hedefe gelince durur.

### Özellikler
- Hedef basınç 0,5–9,0 bar (0,1 adım), kalıcı hafıza (NVS)
- Puls + ölçüm döngüsü; hedefe yaklaştıkça puls kısalır
- kPa / bar / psi gösterim, 2" ST7789V renkli ekran
- Fazla basınç uyarısı (kırmızı "FAZLA! HAVA BOSALT")
- Güvenlik: 10 bar mutlak kesme, sensör kopuk/kısa, lastik takılı değil, basınç artmıyor, 5 dk zaman aşımı
- İsteğe bağlı otomatik tahliye valfi (GPIO26)

### Malzemeler (BOM)
Ayrıntı ve linkler: [`BOM.csv`](BOM.csv). Elektronik + valf ≈ **2.815 TL** (Motorobit, 10/2026).
| Parça | Özellik |
|---|---|
| ESP32 DevKit | ESP-WROOM-32 |
| Solenoid valf | 2W-025-08, 12V DC, NC, G1/4 |
| Basınç sensörü | G1/4, 0–200 psi, 5V, 0,5–4,5V çıkış |
| TIP102 + 1K + 10K + 1N4007 | Valf sürücü |
| 10k + 20k (2×10k) | Sensör bölücü |
| Waveshare 2" ST7789V | 240×320 SPI LCD |
| 3× 16 mm buton, DC jak 5.5×2.1, 12V 2A adaptör, 5V buck | |
| 1/4" fittings | nipeller, 2× T, kör tapa, 3/4→1/4 redüksiyon |

### Bağlantı
| Parça | Bağlantı |
|---|---|
| Güç | 12V adaptör → DC jak; 5V buck → ESP32 VIN + sensör |
| Sensör | sinyal → 10k → GPIO34 → 20k → GND |
| Valf | GPIO25 → 1K → TIP102 B; B → 10K → GND; E → GND; C → valf(−); valf(+) → 12V; 1N4007 katot +12V |
| Butonlar | GPIO32 +, GPIO33 −, GPIO27 START → GND |
| Ekran | VCC 3V3, DIN 23, CLK 18, CS 5, DC 16, RST 17, BL 4 |

| | | |
|---|---|---|
| ![](wiring/1_guc.png) | ![](wiring/2_valf.png) | ![](wiring/3_sensor.png) |
| ![](wiring/4_butonlar.png) | ![](wiring/5_ekran.png) | |

### Derleme / yükleme
```bash
pip install platformio
cd firmware
pio run -t upload
pio device monitor
```
Kullanım: `+`/`−` hedef · `START` kısa: başlat/durdur · `START` uzun: birim.

### Baskı
`enclosure/3mf/` içinde iki tabla (PrusaSlicer/Bambu Studio). PLA: 0,28 mm, 2 duvar, %8 gyroid, 3 üst/3 alt, 220/60 °C, destek yok (`pla.ini`). Gövde ~6,5 sa / 269 g, kapak+kelepçe+takoz ~2,8 sa / 134 g. PETG: 245/75 °C (`petg.ini`). Model kaynak: `enclosure/kutu.py` (CadQuery).

### Kalibrasyon
1. Hortum basınçsızken `+` ve `−` basılı tutarak aç → sıfır kaydedilir.
2. Güvenilir bir manometre ile karşılaştır; gerekiyorsa `main.cpp` içindeki `SENSOR_BAR_MAX` / `SENSOR_V_MIN` değerlerini düzelt.

### Güvenlik
- Kompresör çıkışı ≤10 bar olmalı; hatta mekanik emniyet ventili kullan.
- Lastiğin üzerindeki azami basıncı asla aşma. Bu cihaz yardımcıdır, ölçümü kontrol et.
- PLA ~55 °C'de yumuşar: güneşten, sıcak araç içinden ve kompresörden uzak tut ya da PETG bas.

### Gelecek: tahliye valfi
Büyük 2W-160-15 (G1/2) şişirme valfi olur, küçük valf tahliye T'sine taşınır (susturucu yan duvardaki kırılabilir zardan çıkar). 2. TIP102 + 1N4007 + 1K + 10K → GPIO26. `platformio.ini` içinde `build_flags = -DTAHLIYE_VALFI=1` satırını aç.

---

## English

### Overview
An ESP32 station that sits on a compressor line and inflates a tire to a set pressure. Set the target with the buttons and press START: a 12 V normally-closed solenoid valve opens in short pulses, pressure settles and is measured after each pulse, and it stops at the target.

### Features
- Target 0.5–9.0 bar (0.1 steps), stored in NVS
- Pulse-and-measure loop with pulses shortening near the target
- kPa / bar / psi display on a 2" ST7789V color LCD
- Over-pressure warning (red "FAZLA! HAVA BOSALT" = "too high, release air")
- Safety: 10 bar hard cut-off, sensor open/short detection, no-tire detection, no-rise detection, 5-minute timeout
- Optional automatic exhaust valve on GPIO26

### Bill of materials
See [`BOM.csv`](BOM.csv) (Turkish sellers, prices in TRY). Electronics + valve ≈ 2,815 TRY (10/2026). Main parts: ESP32 DevKit; 2W-025-08 12 V NC G1/4 valve; G1/4 0–200 psi 0.5–4.5 V pressure sensor; TIP102 + 1 kΩ + 10 kΩ + 1N4007; 10 kΩ/20 kΩ divider; Waveshare 2" ST7789V; 3× 16 mm push buttons; 5.5×2.1 DC jack; 12 V 2 A adapter; 5 V buck; 1/4" fittings.

### Wiring
| Part | Connection |
|---|---|
| Power | 12 V adapter → DC jack; 5 V buck → ESP32 VIN + sensor |
| Sensor | signal → 10k → GPIO34 → 20k → GND |
| Valve | GPIO25 → 1K → TIP102 B; B → 10K → GND; E → GND; C → valve(−); valve(+) → 12 V; 1N4007 across valve, cathode to +12 V |
| Buttons | GPIO32 +, GPIO33 −, GPIO27 START → GND (internal pull-ups) |
| Display | VCC 3V3, DIN 23, CLK 18, CS 5, DC 16, RST 17, BL 4 |

Diagrams are in [`wiring/`](wiring) (labels in Turkish: GÜÇ = power, VALF = valve, BUTONLAR = buttons, EKRAN = display).

### Build and flash
```bash
pip install platformio
cd firmware
pio run -t upload
pio device monitor
```
Usage: `+`/`−` sets the target · `START` short press: start/stop · `START` long press: cycle units.

### Printing
Two plates in `enclosure/3mf/`. PLA: 0.28 mm layers, 2 walls, 8 % gyroid, 3 top/3 bottom, 220/60 °C, no supports (`pla.ini`). Body ~6.5 h / 269 g; lid + clamps + spacer ~2.8 h / 134 g. PETG: 245/75 °C (`petg.ini`). Parametric source: `enclosure/kutu.py` (CadQuery; run it, then `render.py` for previews). File names: govde = body, kapak = lid, kelepce = clamp, takoz = valve spacer.

### Calibration
1. With the hose unpressurized, power on while holding `+` and `−` to store the zero offset.
2. Compare against a trusted gauge and adjust `SENSOR_BAR_MAX` / `SENSOR_V_MIN` in `main.cpp` if needed.

### Safety notes
- Compressor output must be ≤10 bar; use a mechanical relief valve on the line.
- Never exceed the maximum pressure printed on the tire. Double-check readings.
- PLA softens around 55 °C: keep it out of the sun, hot cars and away from the compressor, or print in PETG.

### Future upgrade: exhaust valve
The larger 2W-160-15 (G1/2) becomes the inflate valve and the small valve moves to the exhaust tee (muffler exits through the break-out membrane in the side wall). Add a second TIP102 + 1N4007 + 1K + 10K on GPIO26 and enable `build_flags = -DTAHLIYE_VALFI=1` in `platformio.ini`.

## License
Code: MIT. Hardware & docs: CC BY 4.0. © 2026 esp32-tire-inflator contributors. See [LICENSE](LICENSE).
