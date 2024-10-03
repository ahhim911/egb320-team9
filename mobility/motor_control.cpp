#include <Wire.h>
#include <Servo.h>

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0         // Use GPIO 26 as SDA
#define I2C_SCL 1         // Use GPIO 27 as SCL
#define EN1 20
#define PHS1 19
#define EN2 17
#define PHS2 16
#define width 0.14
volatile int last_pos = 45;
int gripservoPin = 9;  // Pin where the servo is connected
int liftservoPin = 10;
Servo gripServo;  
Servo liftServo;



void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

uint8_t waitingflag = 1;

void setup() {
  // Attach servos

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




void ControlSystem(uint8_t* command, int length) {
  // Convert the received command to a string
  char text[length + 1];
  for (int i = 0; i < length; i++) {
    text[i] = (char)command[i];  // Cast each integer to char and store in text
  }
  text[length] = '\0';  // Null-terminate the string
  Serial.println(text);

  char SpeedFor[4] = { text[1], text[2], text[3], '\0' };  // Extract speed value
  int speedfor = atoi(SpeedFor);
  char SpeedRot[4] = { text[5], text[6], text[7], '\0' };  // Extract speed value
  int speedrot = atoi(SpeedRot);// done in percentages where 0 - 100 percentage forwards or rotational velocity
  

  int speed1 = round(speedfor*2.55 + (((speedrot*2.55) * width)/2)); //calcualted output functions for left and right motors based on forwards and rotaional velocities
  int speed2 = round(speedfor*2.55 - (((speedrot*2.55) * width)/2));

  speed1 = constrain(speed1, -255, 255);
  speed2 = constrain(speed2, -255, 255)
  if(speed1 < 0){
    digitalWrite(PHS1, LOW);
    analogWrite(EN1, abs(speed1));
  }else{
    digitalWrite(PHS1, HIGH);
    analogWrite(EN1, abs(speed1));
  }
    if(speed2 < 0){
    digitalWrite(PHS2, LOW);
    analogWrite(EN2, abs(speed2));
  }else{
    digitalWrite(PHS2, HIGH);
    analogWrite(EN2, abs(speed2));;
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