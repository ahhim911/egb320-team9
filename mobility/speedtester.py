#include <Wire.h>
#include <Servo.h>

#define I2C_ADDRESS 0x08  // I2C address of the device
#define I2C_SDA 0         // Use GPIO 26 as SDA
#define I2C_SCL 1         // Use GPIO 27 as SCL
#define EN1 20
#define PHS1 19
#define EN2 17
#define PHS2 16

volatile int last_pos = 45;
int gripservoPin = 9;  // Pin where the servo is connected
int liftservoPin = 10;
Servo gripServo;  
Servo liftServo;

void receiveEvent(int howMany);
void ControlSystem(uint8_t* command, int length);

uint8_t waitingflag = 1;

void setup() {
  Wire.setSDA(I2C_SDA);
  Wire.setSCL(I2C_SCL);
  Wire.begin(I2C_ADDRESS);  

  
  Wire.onReceive(receiveEvent);

  Serial.begin(115200);  

  
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
  
  char text[length + 1];
  for (int i = 0; i < length; i++) {
    text[i] = (char)command[i];  
  }
  text[length] = '\0';  
  Serial.println(text);

  char Speed1Val[4] = { text[2], text[3], text[4], '\0' };  
  char Speed2Val[4] = { text[6], text[7], text[8], '\0' };  

  int speed1 = atoi(Speed1Val);  
  int speed2 = atoi(Speed2Val);  

  speed1 = constrain(speed1, 0, 255);
  speed2 = constrain(speed2, 0, 255);


  if (text[1]=='P') {
    digitalWrite(PHS1, HIGH);       
    analogWrite(EN1, abs(speed1));  
  } else if (text[1] =='N') {
    digitalWrite(PHS1, LOW);       
    analogWrite(EN1, speed1);       
  }
 
  
  if (text[5] =='P') {
    digitalWrite(PHS2, HIGH);       
    analogWrite(EN2, abs(speed2));  
  } else if (text[5] =='N'){
    digitalWrite(PHS2, HIGH);     
    analogWrite(EN2, speed2);      
  }
}

void receiveEvent(int howMany) {
  if (howMany >= 7) {  
    waitingflag = 0;       
    uint8_t cmd[howMany];  
    for (int i = 0; i < howMany; i++) {
      if (Wire.available()) {
        cmd[i] = Wire.read();  
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