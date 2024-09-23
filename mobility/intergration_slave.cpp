#include <Wire.h>

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0        // Use GPIO 26 as SDA
#define I2C_SCL 1        // Use GPIO 27 as SCL
#define EN1 20
#define PHS1 19
#define EN2 17
#define PHS2 16
#define width 0.2
#define WHEEL_BASE 0.15  // Distance between wheels in meters
#define WHEEL_RADIUS 0.04  // Radius of the wheels in meters
#define MAX_WHEEL_SPEED 10 
#define SCALING_FACTOR 127.5



void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

uint8_t waitingflag = 1;

void setup() {


  // Set up I2C on specific pins for the Raspberry Pi Pico
  Wire.setSDA(I2C_SDA);
  Wire.setSCL(I2C_SCL);
  Wire.begin(I2C_ADDRESS);  // Initialize I2C communication

  // Attach a function to the receive event
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);  // Initialize serial communication for debugging


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

void driveint(int left_motor_speed, int right_motor_speed){
    // Control motor 1 (left motor)
  if (motor_left < 0) {
    digitalWrite(PHS1, LOW);  // Reverse direction
  } else {
    digitalWrite(PHS1, HIGH); // Forward direction
  }
  analogWrite(EN1, abs(motor_left));  // Set the speed with PWM

  // Control motor 2 (right motor)
  if (motor_right < 0) {
    digitalWrite(PHS2, LOW);  // Reverse direction
  } else {
    digitalWrite(PHS2, HIGH); // Forward direction
  }
  analogWrite(EN2, abs(motor_right));  // Set the speed with PWM
}

void Drive(float x_dot, float theta_dot) {
  // Calculate left and right wheel speeds (rad/s) based on forward and rotational velocity
  float leftWheelSpeed = (x_dot - 0.5 * theta_dot * WHEEL_BASE) / WHEEL_RADIUS;
  float rightWheelSpeed = (x_dot + 0.5 * theta_dot * WHEEL_BASE) / WHEEL_RADIUS;
  leftWheelSpeed1 = constrain(round(leftWheelSpeed*SCALING_FACTOR)-255,255);
  rightWheelSpeed1 = constrain(round(rightWheelSpeed*SCALING_FACTOR)-255,255);

    driveint(leftWheelSpeed1, rightWheelSpeed1);

}

void ControlSystem(uint8_t* command, int length) {
// Function to set target velocities in m/s and rad/s (similar to simulation code)
 int x_dot = command[1];
 int theta_dot = command[2];
  // Drive the motors using the calculated wheel speeds
  x_dot1 = x_dot/100;
  theta_dot1 = theta_dot/100;
  Drive(x_dot, theta_dot);
}

void receiveEvent(int howMany) {
  if (howMany >= 2) {
    waitingflag = 0;       // turn off waiting flag because command recieved
    int8_t cmd[howMany];  // Buffer to store received command
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

    ControlSystem(cmd, howMany);
  }
}