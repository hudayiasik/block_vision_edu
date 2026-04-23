/*
 * BlockVision Edu — Robot Firmware v2
 *
 * HC-06 Bluetooth (Klasik SPP) üzerinden komut alır.
 * Web Serial API (Chrome) → Bluetooth COM Port → HC-06 → Arduino
 *
 * Komut Protokolü:
 *   '1' = Ileri (move_up)
 *   '2' = Geri  (move_down)
 *   '3' = Sag   (move_right)
 *   '4' = Sol   (move_left)
 *   '5' = Dur
 *
 * Pin Tanimi:
 *   HC-06 : RX=D2, TX=D3
 *   Motor : IN1=4, IN2=5, IN3=6, IN4=7
 *   LED   : D13 (dahili)
 */

#include <SoftwareSerial.h>

SoftwareSerial bluetooth(2, 3);

#define IN1 4
#define IN2 5
#define IN3 6
#define IN4 7
#define LED_PIN 13

#define ADIM_MS  600   // Duz hareket suresi
#define DONUS_MS 380   // Donus suresi

void setup() {
  Serial.begin(9600);
  bluetooth.begin(9600);
  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  dur();
  // Hazir sinyali: LED yanip soner
  for(int i=0;i<3;i++){ digitalWrite(LED_PIN,HIGH); delay(150); digitalWrite(LED_PIN,LOW); delay(150); }
  Serial.println("BlockVision Robot v2 Hazir");
  Serial.println("1=Ileri 2=Geri 3=Sag 4=Sol 5=Dur");
}

void loop() {
  if (bluetooth.available()) {
    char k = bluetooth.read();
    Serial.print("Komut: "); Serial.println(k);
    switch(k) {
      case '1': adim(true,  false, ADIM_MS);  break;
      case '2': adim(false, false, ADIM_MS);  break;
      case '3': adim(true,  true,  DONUS_MS); break;
      case '4': adim(false, true,  DONUS_MS); break;
      case '5': dur(); break;
    }
  }
}

void adim(bool forward, bool turning, int ms) {
  digitalWrite(LED_PIN, HIGH);
  if (!turning) { if(forward) ileri(); else geri(); }
  else          { if(forward) sag();   else sol();  }
  delay(ms);
  dur();
  digitalWrite(LED_PIN, LOW);
  bluetooth.print('K'); // Tamamlandi sinyali
  Serial.println("OK");
}

void ileri() { digitalWrite(IN1,HIGH);digitalWrite(IN2,LOW); digitalWrite(IN3,HIGH);digitalWrite(IN4,LOW); }
void geri()  { digitalWrite(IN1,LOW); digitalWrite(IN2,HIGH);digitalWrite(IN3,LOW); digitalWrite(IN4,HIGH);}
void sag()   { digitalWrite(IN1,HIGH);digitalWrite(IN2,LOW); digitalWrite(IN3,LOW); digitalWrite(IN4,HIGH);}
void sol()   { digitalWrite(IN1,LOW); digitalWrite(IN2,HIGH);digitalWrite(IN3,HIGH);digitalWrite(IN4,LOW); }
void dur()   { digitalWrite(IN1,LOW); digitalWrite(IN2,LOW); digitalWrite(IN3,LOW); digitalWrite(IN4,LOW);  }
