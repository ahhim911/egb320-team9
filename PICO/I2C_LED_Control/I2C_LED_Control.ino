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
void drive(int speed, int direction) {
  // Scale factor to convert speed and direction to PWM range
  const float scale_factor = MAX_SPEED / MAX_INPUT_SPEED;

  // Constrain direction between -10 and 10
  direction = constrain(direction, -MAX_DIRECTION, MAX_DIRECTION);

  // Scale speed and direction
  int scaled_speed = constrain(speed * scale_factor, -MAX_SPEED, MAX_SPEED);
  int scaled_direction = constrain(direction * scale_factor, -MAX_SPEED, MAX_SPEED);

  int motor_left, motor_right;

  // Calculate motor speeds based on speed and direction
  if (direction < 0) { // Turning left
    motor_left = scaled_speed;
    motor_right = scaled_speed + scaled_direction; // slower on the right
  } else { // Turning right
    motor_right = scaled_speed;
    motor_left = scaled_speed - scaled_direction; // slower on the left
  }

  // Constrain motor speeds between -255 and 255
  motor_left = constrain(motor_left, -MAX_SPEED, MAX_SPEED);
  motor_right = constrain(motor_right, -MAX_SPEED, MAX_SPEED);

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

  // Extract speed value from command
  char Speed1[4] = { text[2], text[3], text[4], '\0' };  // Extract speed value
  int speed1 = atoi(Speed1);

  // Extract direction value from command
  char Direction[4] = { text[6], text[7], text[8], '\0' };  // Extract direction value
  int direction = atoi(Direction);

  if (text[1] == 'N') {
    speed1 = speed1 * -1;  // Negate speed if necessary
  }
  if (text[5] == 'N') {
    direction = direction * -1;  // Negate direction if necessary
  }

  // Call drive function with scaled values
  drive(speed1, direction);


  // Servos control
  if (text[9] == 'O') {
    gripper_open();
  } else if (text[9] == 'C') {
    gripper_close();
  }
  switch (text[10]) {
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

  // LED control
  ledControl(LED1, text[11] == '1');
  ledControl(LED2, text[12] == '1');
  ledControl(LED3, text[13] == '1');
  
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

