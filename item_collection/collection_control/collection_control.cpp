#include <Servo.h> // Include the Servo library

Servo gripServo;  // Create a Servo object
Servo liftServo;

volatile int last_pos = 45;
int gripservoPin = 9;  // Pin where the servo is connected
int liftservoPin = 10;

void setup() {
  gripServo.attach(gripservoPin);  // Attach the servo to the pin
  liftServo.attach(liftservoPin);
  liftServo.write(10);
  gripServo.write(170);
}

void loop(){
  //lift_level1();
  //delay(1000);
  //release_item();
  //lift_level2();
  //delay(1000);
  //release_item();
  lift_level3();
  delay(2000);
  release_item();
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