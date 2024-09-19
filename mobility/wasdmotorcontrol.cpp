#include <Wire.h>

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0         // Use GPIO 26 as SDA
#define I2C_SCL 1         // Use GPIO 27 as SCL
#define EN1 20
#define PHS1 19
#define EN2 17
#define PHS2 16

// Speed for each direction (0-255 for motor speed control)
int speed = 150;

volatile int waitingflag = 1;

void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

void setup() {
  // Set up I2C on specific pins for the Raspberry Pi Pico
  Wire.setSDA(I2C_SDA);
  Wire.setSCL(I2C_SCL);
  Wire.begin(I2C_ADDRESS);  // Initialize I2C communication

  // Attach a function to the receive event
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);  // Initialize serial communication for debugging

  // Setup motor control pins as output
  pinMode(EN1, OUTPUT);
  pinMode(EN2, OUTPUT);
  pinMode(PHS1, OUTPUT);
  pinMode(PHS2, OUTPUT);
}

void loop() {
  if (waitingflag) {
    delay(10);
  }
}

void ControlSystem(uint8_t* command, int length) {
  // Convert the received command to a string
  char text[length + 1];
  for (int i = 0; i < length; i++) {
    text[i] = (char)command[i];  // Cast each integer to char and store in text
  }
  text[length] = '\0';  // Null-terminate the string
  Serial.println(text);

  // WASD Control System
  switch (text[0]) {
    case 'w':  // Move forward
      Serial.println("Moving forward");
      digitalWrite(PHS1, HIGH);   // Set motor 1 forward direction
      digitalWrite(PHS2, HIGH);   // Set motor 2 forward direction
      analogWrite(EN1, speed);    // Set motor 1 speed
      analogWrite(EN2, speed);    // Set motor 2 speed
      break;

    case 's':  // Move backward
      Serial.println("Moving backward");
      digitalWrite(PHS1, LOW);    // Set motor 1 backward direction
      digitalWrite(PHS2, LOW);    // Set motor 2 backward direction
      analogWrite(EN1, speed);    // Set motor 1 speed
      analogWrite(EN2, speed);    // Set motor 2 speed
      break;

    case 'a':  // Turn left
      Serial.println("Turning left");
      digitalWrite(PHS1, LOW);    // Set motor 1 backward direction
      digitalWrite(PHS2, HIGH);   // Set motor 2 forward direction
      analogWrite(EN1, speed);    // Set motor 1 speed
      analogWrite(EN2, speed);    // Set motor 2 speed
      break;

    case 'd':  // Turn right
      Serial.println("Turning right");
      digitalWrite(PHS1, HIGH);   // Set motor 1 forward direction
      digitalWrite(PHS2, LOW);    // Set motor 2 backward direction
      analogWrite(EN1, speed);    // Set motor 1 speed
      analogWrite(EN2, speed);    // Set motor 2 speed
      break;

    case 'x':  // Stop
      Serial.println("Stopping");
      analogWrite(EN1, 0);        // Stop motor 1
      analogWrite(EN2, 0);        // Stop motor 2
      break;

    default:
      Serial.println("Unknown command");
      break;
  }
}

void receiveEvent(int howMany) {
  if (howMany >= 1) {
    waitingflag = 0;       // Turn off waiting flag because a command was received
    uint8_t cmd[howMany];  // Buffer to store received command
    for (int i = 0; i < howMany; i++) {
      if (Wire.available()) {
        cmd[i] = Wire.read();  // Read received byte
      }
    }
    Serial.print("Received command: ");
    for (int i = 0; i < howMany; i++) {
      Serial.print((char)cmd[i]);
    }
    Serial.println();

    // Process the received command
    ControlSystem(cmd, howMany);
  }
}
