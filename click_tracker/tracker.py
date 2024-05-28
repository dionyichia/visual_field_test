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