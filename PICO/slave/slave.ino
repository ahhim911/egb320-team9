#include <Wire.h>
#include <Servo.h> // Include the Servo library

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0        // Use GPIO 26 as SDA
#define I2C_SCL 1        // Use GPIO 27 as SCL
#define EN1 20
#define PHS1 19
#define EN2 17
#define PHS2 16
#define WIDTH 0.2
#define MAX_SPEED 255      // Maximum PWM value for motor speed
#define MAX_INPUT_SPEED 100 // Maximum input speed value (user input scale)
#define MAX_DIRECTION 100 
#define WHEEL_BASE 0.15  // Distance between wheels in meters
#define WHEEL_RADIUS 0.04  // Radius of the wheels in meters
#define MAX_WHEEL_SPEED 10 
#define SCALING_FACTOR 127.5

volatile int last_pos = 45;
int gripservoPin = 9;  // SV1
int liftservoPin = 10; // SV2
int LED1 = 4;
int LED2 = 5;
int LED3 = 6;
Servo gripServo;  
Servo liftServo;

void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

uint8_t waitingflag = 1;

void setup() {
  // Attach servos
  gripServo.attach(gripservoPin);  // Attach the servo to the pin
  liftServo.attach(liftservoPin);
  liftServo.write(10);
  gripServo.write(170);

  // Set up LED direction
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  // Set up I2C on specific pins for the Raspberry Pi Pico
  Wire.setSDA(I2C_SDA);
  Wire.setSCL(I2C_SCL);
  Wire.begin(I2C_ADDRESS);  // Initialize I2C communication

  // Attach a function to the receive event
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);  // Initialize serial communication for debugging

  // Setup LED 0,1,2,3 as output and turn LED off initially

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

// LED control function
void ledControl(int led, int state) {
  digitalWrite(led, state);
}


// Drive function that scales speed and direction
void driveint(int left_motor_speed, int right_motor_speed){
    // Control motor 1 (left motor)
  if (left_motor_speed < 0) {
    digitalWrite(PHS1, LOW);  // Reverse direction
  } else {
    digitalWrite(PHS1, HIGH); // Forward direction
  }
  analogWrite(EN1, abs(left_motor_speed));  // Set the speed with PWM

  // Control motor 2 (right motor)
  if (right_motor_speed < 0) {
    digitalWrite(PHS2, LOW);  // Reverse direction
  } else {
    digitalWrite(PHS2, HIGH); // Forward direction
  }
  analogWrite(EN2, abs(right_motor_speed));  // Set the speed with PWM
}

void Drive(float x_dot, float theta_dot) {
  // Calculate left and right wheel speeds (rad/s) based on forward and rotational velocity
  float leftWheelSpeed = (x_dot - 0.5 * theta_dot * WHEEL_BASE) / WHEEL_RADIUS;
  float rightWheelSpeed = (x_dot + 0.5 * theta_dot * WHEEL_BASE) / WHEEL_RADIUS;
  float leftWheelSpeed1 = constrain(round(leftWheelSpeed*SCALING_FACTOR),-255,255);
  float rightWheelSpeed1 = constrain(round(rightWheelSpeed*SCALING_FACTOR),-255,255);

    driveint(leftWheelSpeed1, rightWheelSpeed1);

}



void gripper_close() {
  // Move servo to 90 degrees
  gripServo.write(0);  
  delay(1000);  // Wait for a second
}

void gripper_open(){
   gripServo.write(170);  
  delay(1000);  // Wait for a second
}

void lift_level3(){
  move_lift(160);
  delay(1000);
}

void lift_level2(){
  move_lift(90);
  delay(1000);
}

void lift_level1(){
  move_lift(10);
  delay(1000);
}

void release_item(){
  lift_level1();
  delay(1000);
  gripper_open();
}

void move_lift(int target_pos){
  if (last_pos < target_pos){ // Moving UP
    int delta = target_pos - last_pos;
    for (uint8_t i = 0; i < delta; i++){
      liftServo.write(last_pos + i);
      delay(20);
    }
  } else {
    int delta = last_pos - target_pos;
    for (uint8_t i = 0; i < delta; i++){
      liftServo.write(last_pos - i);
      delay(20);
    }
  }
  last_pos = target_pos;
}


//================================================
// Control system function
//================================================


void ControlSystem(uint8_t* command, int length) {
  // Convert the received command to a string
  char text[length + 1];
  for (int i = 0; i < length; i++) {
    text[i] = (char)command[i];  // Cast each integer to char and store in text
  }
  text[length] = '\0';  // Null-terminate the string
  Serial.println(text);

  switch (text[1]) {
    
    // Drive command
    case 'D': {
      // Function to set target velocities in m/s and rad/s (similar to simulation code)
      int x_dot = text[2];
      int theta_dot = text[3];
      // Drive the motors using the calculated wheel speeds
      float x_dot1 = x_dot/100;
      float theta_dot1 = theta_dot/100;
      Drive(x_dot, theta_dot);
      break;
    }
    // Gripper control
    case 'G': {
      if (text[2] == '0') {
        gripper_open();
      } else if (text[2] == '1') {
        gripper_close();
      }
      break;
    }
    // Lift control
    case 'H': {
      switch (text[2]) {
        case '1':
          lift_level1();
          break;
        case '2':
          lift_level2();
          break;
        case '3':
          lift_level3();
          break;
        default:
          Serial.println("Invalid Given Index");
          break;
      }
      break;
    }
    //LED control
    case 'L': {
      int led;
      switch (text[2]) {
        case '1':
          led = LED1;
          break;
        case '2':
          led = LED2;
          break;
        case '3':
          led = LED3;
          break;
        default:
          Serial.println("Invalid Given Index");
          break;
      }
      if (text[3] == '1') {
        ledControl(led, HIGH);
      } else if (text[3] == '0') {
        ledControl(led, LOW);
      }
      break;
    }
    default:{
      Serial.println("Invalid Command");
      break;
    }
  }
}



void receiveEvent(int howMany) {
  if (howMany >= 2) {
    waitingflag = 0;       // turn off waiting flag because command recieved
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

    ControlSystem(cmd, howMany);
  }
}

