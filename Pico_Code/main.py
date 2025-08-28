from pico_usb_serial import serial
from robot_arm_class import RobotArm,Servo_MA
from time import sleep
import machine


servo1 = Servo_MA(pwm_pin=16, min_us=500, max_us=2500, freq=50)
servo2 = Servo_MA(pwm_pin=1, min_us=500, max_us=2500, freq=50)

s1_value = 0
s2_value = 0


onboard_led = machine.Pin("LED", machine.Pin.OUT)

def parse_serial_data(data_string):
    global s1_value, s2_value
    """Parse serial data in format 'S1 90, S2 90' or 'S1 90, S2 90/n'"""
    try:
        # Remove any trailing newline characters
        data_string = data_string.strip().replace('/n', '').replace('\n', '')
        
        # Split by comma to get individual sensor readings
        parts = data_string.split(',')
        print("Parts:", parts)
        
        
        for part in parts:
            part = part.strip()
            if part.startswith('S1'):
                s1_value = int(part.split()[1])
            elif part.startswith('S2'):
                s2_value = int(part.split()[1])
        
        return s1_value, s2_value
    except (ValueError, IndexError):
        return s1_value, s2_value  # Return previous values on error


while True:
    if serial.available():
        line = serial.read_line(timeout=0.1)
        serial.println(f"You entered: {line}")
        s1_value, s2_value = parse_serial_data(line)
        print(f"Parsed S1: {s1_value}, S2: {s2_value}")
        try:
            if s1_value is not None:
                servo1.set_angle(s1_value)
            if s2_value is not None:
                servo2.set_angle(s2_value)
        except Exception as e:
            print("Error setting servo angle:", e)



    else:
        ##serial.println("No data available")
        sleep(0.1)
        onboard_led.toggle()
        continue

        


