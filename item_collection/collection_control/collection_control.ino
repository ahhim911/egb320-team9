#include <Servo.h> // Include the Servo library

Servo gripServo;  // Create a Servo object
Servo liftServo;

volatile int last_pos = -5;
int gripservoPin = 9;  // Pin where the servo is connected
int liftservoPin = 10;

void setup() {
  gripServo.attach(gripservoPin);  // Attach the servo to the pin
  liftServo.attach(liftservoPin);
  liftServo.write(0); //

}

void loop(){
  //gripper_close();
  //gripper_open();
  //lift_level1();
  //delay(1000);
  //lift_level2();
  //delay(1000);
  //lift_level3();
  //delay(2000);
  //lift_level2();
  //delay(1000);
  //lift_level1();
  //delay(1000);
  liftServo.write(180);
}
 

void gripper_close() {
  // Move servo to 90 degrees
  gripServo.write(80);  
  delay(1000);  // Wait for a second

  // Move servo to 0 degrees
  gripServo.write(0);  
  delay(1000);  // Wait for a second

}
void gripper_open(){
   gripServo.write(0);  
  delay(1000);  // Wait for a second

  // Move servo to 0 degrees
  gripServo.write(80);  
  delay(1000);  // Wait for a second

}

void lift_level3(){
  
  move_lift(85);
  delay(1000);
}

void lift_level2(){
  move_lift(-5);
  delay(1000);
}

void lift_level1(){
  move_lift(-50);
  delay(1000);
}

void move_lift(int target_pos){
  if (last_pos < target_pos){ // Moving UP
    int delta = target_pos - last_pos;
    for (uint8_t i = 0; i < delta; i++){
      liftServo.write(last_pos + i);
      delay(10);
    }
  } else {
    int delta = last_pos - target_pos;
    for (uint8_t i = 0; i < delta; i++){
      liftServo.write(last_pos - i);
      delay(10);
    }
  }
  last_pos = target_pos;



}