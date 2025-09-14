from pico_usb_serial import serial
from robot_arm_class import RobotArm,Servo_MA
from time import sleep
import machine
import time



servo1 = Servo_MA(pwm_pin=16, min_us=500, max_us=2500, freq=50)
servo2 = Servo_MA(pwm_pin=17, min_us=500, max_us=2500, freq=50)

servo1.set_angle(90)
servo2.set_angle(90)








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

s1_value = 90
s2_value = 90
start_time = time.ticks_ms()
while True:
    if serial.available():
        line = serial.read_line(timeout=0.1)
        serial.println(f"You entered: {line}")
        s1_value, s2_value = parse_serial_data(line)
        print(f"Parsed S1: {s1_value}, S2: {s2_value}")

    try:
        if s1_value is not None:
            servo1.set_angle_smooth(s1_value, smoothing_factor=0.02)
        if s2_value is not None:
            servo2.set_angle_smooth(s2_value,smoothing_factor=0.02)
    except Exception as e:
        print("Error setting servo angle:", e)



    else:
        ##serial.println("No data available")
        #sleep(0.01)
        if time.ticks_diff(time.ticks_ms(), start_time) > 100:
            start_time = time.ticks_ms()
            onboard_led.toggle()
        continue

        


