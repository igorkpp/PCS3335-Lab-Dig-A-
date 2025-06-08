#include <SoftwareSerial.h>

const int txPin = 10;
SoftwareSerial uart_fpga(-1, txPin);

void setup() {
  Serial.begin(9600);
  uart_fpga.begin(9600);
  pinMode(txPin, OUTPUT);
  Serial.println("Arduino UART bridge pronto.");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    uart_fpga.write(c);
    Serial.print(c);
  }
}