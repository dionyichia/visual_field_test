import time
import sys
import serial

# Connect to Arduino
arduino_port = '/dev/cu.usbserial-130'  # Change this to the correct port
baud_rate = 9600
try:
    arduino = serial.Serial(arduino_port, baud_rate)
except:
    print("Unable to connect to port")

def read_button_state():
    # Read data from Arduino
    button_state = arduino.readline().decode().strip()

    # Process button state
    if button_state == 'ON':
        print("Button is pressed")

        return True
    elif button_state == '0FF':
        print("Button is not pressed")
        return False

def readtime(start_time):
    click_time = time.time() - start_time   
    return click_time

if __name__ == "__main__":

    # Now continuously check the button state while waiting for the timing window
    start_time = time.time()
    print("Click the button between 1 and 3 seconds into the runtime.")

    click_time = []
    while True:
        button_pressed = read_button_state()
        if button_pressed:
            click_time.append(readtime(start_time))
        
        if(readtime(start_time) >= 5):
            break

    
    if 1 <= click_time[0] <= 3:
        print("Passed, Result:", click_time)
    else:
        print("Fail, Result:", click_time)

"""
Arduino code: Clicker Button to Video Timing
 // declare pins
 const int button_pin = 4;

// variable for button state
int button_state;

void setup() { // put your setup code here, to run once:
  pinMode(button_pin,INPUT);  // set button pin as input
  Serial.begin(9600);
}

void loop() { // put your main code here, to run repeatedly:
  button_state = digitalRead(button_pin);  // read button state
  if(button_state == HIGH){           // if button is pushed
    Serial.println("ON");
  }
  else{                               // if button is not pushed
    Serial.println("OFF");
  }
}

"""

"""
Arduino Code: Button to 4 LEDs
 // declare pins
const int button_pin = 7;
const int led1 = 3;
const int led2 = 4;
const int led3 = 5;
const int led4 = 6;

// variable for button state
int button_state;
int led1_state;
int led2_state;
int led3_state;
int led4_state;
int counter;

void setup() { // put your setup code here, to run once:
  pinMode(button_pin,INPUT);  // set button pin as input
  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT);
    Serial.begin(9600);
}

void loop() { // put your main code here, to run repeatedly:
  button_state = digitalRead(button_pin);  // read button state
  if(button_state == HIGH){           // if button is pushed
    Serial.println("ON");
    digitalWrite(led1, HIGH);
    delay(100);
    digitalWrite(led1, LOW);
    delay(100);
    digitalWrite (led2, HIGH);
    delay(100);
    digitalWrite (led2, LOW);
    delay(100);
    digitalWrite (led3, HIGH);
    delay(100);
    digitalWrite (led3, LOW);
    delay(100);
    digitalWrite (led4, HIGH);
    delay(100);
    digitalWrite (led4, LOW);
  }
  else{                               // if button is not pushed
    Serial.println("OFF");
    digitalWrite (led1, LOW);    
    digitalWrite (led2, LOW);
    digitalWrite (led3, LOW);
    digitalWrite (led4, LOW);
  }
}

"""