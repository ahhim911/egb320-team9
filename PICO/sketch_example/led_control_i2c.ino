#include <Wire.h>
#define I2C_ADDRESS 0x08
#define LED 25


void receiveEvent(int howMany);

void setup() {
  // Join I2C bus as slave with address 0x08
  Wire.setSDA(0);
  Wire.setSCL(1);
  Wire.begin(I2C_ADDRESS);
  
  // Call receiveEvent when data is received
  Wire.onReceive(receiveEvent);
  Serial.begin(115200);
  
  // Setup pin 25 as output and turn LED off
  pinMode(LED, OUTPUT);  
  digitalWrite(LED, LOW); // Start with LED off
}

static char buff[100];  // Global buffer to store received data

void loop() {

}

void receiveEvent(int howMany) {
  // Ensure at least 2 bytes are received
  if (howMany >= 2) {
    uint8_t cmd[100]; // Buffer to store received command
    for (int i = 0; i < howMany; i++) {
      cmd[i] = Wire.read(); // Read received byte
    }
    // Print received command as characters for clarity
    Serial.print("Received command: ");
    for (int i = 0; i < howMany; i++) {
      Serial.print((char)cmd[i]);
    }
    Serial.println();
    
    // Compare received characters
    if (cmd[1] == 'O' && cmd[2] == 'N') {
      digitalWrite(LED, HIGH); // Turn on LED
    } else if (cmd[1] == 'O' && cmd[2] == 'F') {
      digitalWrite(LED, LOW); // Turn off LED
    }
  }
}