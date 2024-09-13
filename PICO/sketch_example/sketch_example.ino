#include <Wire.h>
#define I2C_ADDRESS 0x08

void receiveEvent(int howMany);

void setup() {
  // Join I2C bus as slave with address 0x08
  Wire.setSDA(0);
  Wire.setSCL(1);
  Wire.begin(I2C_ADDRESS);
  
  // Call receiveEvent when data is received
  Wire.onReceive(receiveEvent);
  Serial.begin(115200);
}

void loop() {
  // Nothing to do in the loop, waiting for I2C events
}

void receiveEvent(int howMany) {
  // Buffer to store received command
  char cmd[100]; 

  // Read all received bytes
  for (int i = 0; i < howMany; i++) {
    cmd[i] = Wire.read(); // Read received byte
  }
  
  // Null-terminate the string for safe printing
  cmd[howMany] = '\0';

  // Print received command as characters
  Serial.print("Received command: ");
  Serial.println(cmd);
}