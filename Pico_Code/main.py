from pico_usb_serial import serial
from robot_arm_class import RobotArm,Servo_MA
from time import sleep
import machine
import time



J1 = Servo_MA(pwm_pin=0, joint_number="1",min_us=500, max_us=2500, freq=50)
J2= Servo_MA(pwm_pin=1, joint_number="2",min_us=500, max_us=2500, freq=50)
J3= Servo_MA(pwm_pin=2, joint_number="3",min_us=500, max_us=2500, freq=50)
J4= Servo_MA(pwm_pin=3, joint_number="4",min_us=500, max_us=2500, freq=50)
J5= Servo_MA(pwm_pin=5, joint_number="5",min_us=500, max_us=2500, freq=50)

J1.set_angle(90)
J2.set_angle(90)
J3.set_angle(90)
J4.set_angle(90)
J5.set_angle(90)








onboard_led = machine.Pin("LED", machine.Pin.OUT)

def parse_serial_data(data_string):
    global s1_value, s2_value,s3_value,s4_value,s5_value
    """Parse serial data in format 'S1 90, S2 90' or 'S1 90, S2 90/n'"""
    #try:
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
        elif part.startswith('S3'):
            s3_value = int(part.split()[1])
            pass
        elif part.startswith('S4'):
            s4_value = int(part.split()[1])
        elif part.startswith('S5'):
            #s5_value = int(part.split()[1])
            s5_value = None
            pass
    return s1_value, s2_value,s3_value,s4_value,s5_value
    #except (ValueError, IndexError):
        #return s1_value, s2_value,s3_value,s4_value,s5_value # Return previous values on error

s1_value = 90
s2_value = 90
s3_value = None
s4_value = 90
s5_value = None
start_time = time.ticks_ms()
while True:
    if serial.available():
        line = serial.read_line(timeout=0.1)
        serial.println(f"You entered: {line}")
        s1_value, s2_value,s3_value,s4_value,s5_value = parse_serial_data(line)
        print(f"Parsed S1: {s1_value}, S2: {s2_value},S3: {s3_value},S4: {s4_value},S5: {s5_value}")

    try:
        if s1_value is not None and J1 is not None:
            J1.set_angle_smooth(s1_value, smoothing_factor=0.01)
        if s2_value is not None and J2 is not None:
            J2.set_angle_smooth(s2_value,smoothing_factor=0.005)
        if s3_value is not None and J3 is not None:
            J3.set_angle_smooth(s3_value,smoothing_factor=0.01)
        if s4_value is not None and J4 is not None:
            J4.set_angle_smooth(s4_value,smoothing_factor=0.01)
    except Exception as e:
        print("Error setting servo angle:", e)



    else:
        ##serial.println("No data available")
        #sleep(0.01)
        if time.ticks_diff(time.ticks_ms(), start_time) > 100:
            start_time = time.ticks_ms()
            onboard_led.toggle()
        continue

        


