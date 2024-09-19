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






//   switch (text[1]) {


//     case 'M':
//       {

//         /* Example Command of Motor Control: 
//               M1 1 255 -> Set speed of Motor 1 to full speed, Anticlockwise
//               M2 0 0 -> Set speed of Motor 2 to low speed, Clockwise
//               M1 S -> Stop motor 1
//               #Syntax: M<ID> <Direction> <Speed>
//               */

//         if (length > 4) {            // Ensure the command has sufficient length
//           char Direction = text[4];  // Get the direction ('0', '1', or 'S')

//           if (Direction != 'S') {                                 // If not stop command
//             char Speed[4] = { text[6], text[7], text[8], '\0' };  // Extract speed value
//             int speed = atoi(Speed);                              // Convert speed to integer

//             switch (text[2]) {
//               case '1':
//                 if (Direction == '0') {
//                   digitalWrite(PHS1, HIGH);  // Set Direction
//                 } else if (Direction == '1') {
//                   digitalWrite(PHS1, LOW);  // Set Direction
//                 }
//                 analogWrite(EN1, speed);  // Write speed by generating PWM signal
//                 Serial.print("Motor 1 set to direction ");
//                 Serial.print(Direction);
//                 Serial.print(" with speed ");
//                 Serial.println(speed);
//                 break;

//               case '2':
//                 if (Direction == '0') {
//                   digitalWrite(PHS2, HIGH);  // Set Direction
//                 } else if (Direction == '1') {
//                   digitalWrite(PHS2, LOW);  // Set Direction
//                 }
//                 analogWrite(EN2, speed);  // Write speed by generating PWM signal
//                 Serial.print("Motor 2 set to direction ");
//                 Serial.print(Direction);
//                 Serial.print(" with speed ");
//                 Serial.println(speed);
//                 break;

//               default:
//                 Serial.println("Invalid motor index");
//                 break;
//             }
//           } else if (Direction == 'S') {  // Stop command 'S'
//             switch (text[2]) {
//               case '1':
//                 analogWrite(EN1, 0);  // Stop Motor 1
//                 Serial.println("Motor 1 stopped");
//                 break;
//               case '2':
//                 analogWrite(EN2, 0);  // Stop Motor 2
//                 Serial.println("Motor 2 stopped");
//                 break;
//               default:
//                 Serial.println("Invalid motor index");
//                 break;
//             }
//           }
//         } else {
//           Serial.println("Invalid command length for motor");
//         }
//         break;
//       }


//     default:
//       Serial.println("Unknown command received");
//       break;
//   }
// }

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



// #include <Wire.h>
// // #include <Servo.h>
// #define I2C_ADDRESS 0x08  // I2C address of the device
// #define I2C_SDA 0         // Use GPIO 26 as SDA
// #define I2C_SCL 1         // Use GPIO 27 as SCL
// #define EN1 20
// #define PHS1 19
// #define EN2 17
// #define PHS2 16
// #define width 0.5
// int speedfor = 0;  // Forward speed
// int speedrot = 0;  // Rotational speed


// void receiveEvent(int howMany);
// void ControlSystem(uint8_t* command, int length);

// uint8_t waitingflag = 1;

// void setup() {
//   // Attach servos
//   // gripServo.attach(gripservoPin);  // Attach the servo to the pin
//   // liftServo.attach(liftservoPin);
//   // liftServo.write(10);
//   // gripServo.write(170);

//   // Set up I2C on specific pins for the Raspberry Pi Pico
//   Wire.setSDA(I2C_SDA);
//   Wire.setSCL(I2C_SCL);
//   Wire.begin(I2C_ADDRESS);  // Initialize I2C communication

//   // Attach a function to the receive event
//   Wire.onReceive(receiveEvent);

//   Serial.begin(115200);  // Initialize serial communication for debugging

//   // Setup LED 0,1,2,3 as output and turn LED off initially

//   pinMode(EN1, OUTPUT);
//   pinMode(EN2, OUTPUT);
//   pinMode(PHS1, OUTPUT);
//   pinMode(PHS2, OUTPUT);
// }

// void loop() {
//   if (waitingflag) {
//     delay(10);
//   }
// }




// void ControlSystem(uint8_t* command, int length) {
//   // Convert the received command to a string
//   char text[length + 1];
//   for (int i = 0; i < length; i++) {
//     text[i] = (char)command[i];  // Cast each integer to char and store in text
//   }
//   text[length] = '\0';  // Null-terminate the string
//   Serial.println(text);

//   char SpeedFor[4] = { text[3], text[4], text[5], '\0' };  // Extract speed value
//   int speedfor1 = atoi(SpeedFor);
//   char SpeedRot[4] = { text[7], text[8], text[9], '\0' };  // Extract speed value
//   int speedrot1 = atoi(SpeedRot);// done in percentages where 0 - 100 percentage forwards or rotational velocity

//   int init_speed1 = round(speedfor*2.55 + (((speedrot*2.55) * width)/2));
//   int init_speed2 = round(speedfor*2.55 - (((speedrot*2.55) * width)/2));
//   int speed1 = constrain(init_speed1, -255, 255);
//   int speed2 = constrain(init_speed2, -255, 255);
//   switch(text[1]){
//   case 'M':
//     if(speed1 < 0){
//     digitalWrite(PHS1, LOW);
//     analogWrite(EN1, abs(speed1));
//   }else{
//     digitalWrite(PHS1, HIGH);
//     analogWrite(EN1, abs(speed1));
//   }
//     if(speed2 < 0){
//     digitalWrite(PHS2, LOW);
//     analogWrite(EN2, abs(speed2));
//   }else{
//     digitalWrite(PHS2, HIGH);
//     analogWrite(EN2, abs(speed2));
//   }
//   break;
//   default:
//   break;

// }






// }
// //   if (text[1] != 'S') {
// //     switch (text[1]) {
// //       case 'N':
// //         digitalWrite(PHS1, LOW);   //sets motor 1 to a reverse direction
// //         analogWrite(EN1, speed1);  //sets the motor to the specified speed
// //         break;
// //       case 'P':
// //         digitalWrite(PHS1, HIGH);  //sets motor 1 to a forwards direction
// //         analogWrite(EN1, speed1);
// //         break;
// //       default:
// //         Serial.println("Invalid Given Index");
// //         break;
// //     }
// //     switch (text[4]) {
// //       case 'P':
// //         digitalWrite(PHS2, HIGH);
// //         analogWrite(EN2, speed2);
// //         break;
// //       case 'N':
// //         digitalWrite(PHS2, LOW);
// //         analogWrite(EN2, speed2);
// //         break;
// //       default:
// //         Serial.println("Invalid Given Index");
// //         break;
// //     }
// //   } else if (text[1] == 'S') {
// //     analogWrite(EN1, 0);
// //     analogWrite(EN1, 0);
// //   }
  
// //   if (text[9] == 'O') {
// //     gripper_open();
// //     switch (text[10]) {
// //       case '1':
// //         lift_level1();
// //         break;
// //       case '2':
// //         lift_level2();
// //         break;
// //       case '3':
// //         lift_level3();
// //         break;
// //       default:
// //         Serial.println("Invalid Given Index");
// //         break;
// //     }
// //   } else if (text[9] == 'C') {
// //     gripper_close();
// //     lift_level1();
// //   }
// // }


// void receiveEvent(int howMany) {
//   if (howMany >= 2) {
//     waitingflag = 0;       // turn off waiting flag because command recieved
//     uint8_t cmd[howMany];  // Buffer to store received command
//     for (int i = 0; i < howMany; i++) {
//       if (Wire.available()) {
//         cmd[i] = Wire.read();  // Read received byte
//       }
//     }
//     Serial.print("Received command: ");
//     for (int i = 0; i < howMany; i++) {
//       Serial.print((char)cmd[i]);
//     }
//     Serial.println();

//     ControlSystem(cmd, howMany);
//   }
// }