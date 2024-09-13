#include <Servo.h> // Include the Servo library
#include <Wire.h>

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0         // Use GPIO 26 as SDA
#define I2C_SCL 1         // Use GPIO 27 as SCL


volatile int last_pos = 45;
int gripservoPin = 9;  // Pin where the servo is connected
int liftservoPin = 10;
Servo gripServo;  
Servo liftServo;


void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

uint8_t waitingflag = 1;

volatile int last_pos = 45;

void setup() {
  // Attach servos
  gripServo.attach(gripservoPin);  // Attach the servo to the pin
  liftServo.attach(liftservoPin);
  liftServo.write(10);
  gripServo.write(170);

  // Set up I2C on specific pins for the Raspberry Pi Pico
  Wire.setSDA(I2C_SDA);
  Wire.setSCL(I2C_SCL);
  Wire.begin(I2C_ADDRESS);  // Initialize I2C communication

  // Attach a function to the receive event
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);  // Initialize serial communication for debugging

  
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

  if (text[9] == 'O') {
    gripper_open();
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
  } else if (text[9] == 'C') {
    gripper_close();
    lift_level1();
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
  move_lift(150);
  delay(1000);
  gripper_close();
}

void lift_level2(){
  move_lift(90);
  delay(1000);
  gripper_close();
}

void lift_level1(){
  move_lift(10);
  delay(1000);
  gripper_close();
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
