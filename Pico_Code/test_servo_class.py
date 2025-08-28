from machine import Pin, PWM
import time
from lib.robot_arm_class import Servo_MA

servo1 = Servo_MA(pwm_pin=16, min_us=500, max_us=2500, freq=50)
# Setup
led = Pin("LED", Pin.OUT)
time.sleep(1)



# Example movement
while True:
    for angle in range(0, 181, 10):  # 0° to 180°
        servo1.set_angle(angle)
        print(f"Moving to {angle}°")
        print(servo1.pwm)
        time.sleep(0.1)
        led.toggle()
    for angle in range(180, -1, -10):  # 180° back to 0°
        led.toggle()
        print(f"Moving to {angle}°")
        servo1.set_angle(angle)
        time.sleep(0.1)

# for i in range(1000,9000,100):
#     servo1.pwm.duty_u16(i)
#     print(f"Moving to {i}us")
#     print(servo1.pwm)
#     time.sleep(0.05)
#     led.toggle()

# TEST_PIN = PWM(Pin(16))
# #TEST_PIN.freq(50)
# TEST_PIN.duty_u16(1000)
#servo1.pwm.freq(50)
