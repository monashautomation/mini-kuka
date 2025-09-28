from machine import Pin, PWM
import time

# Setup
servo = PWM(Pin(18))   # Use GPIO16 (change if needed)
servo.freq(50)         # Standard servo PWM frequency: 50 Hz
led = Pin("LED", Pin.OUT)

def set_angle(angle):
    # angle: 0 - 180
    # Duty cycle: 0.5 ms (0°) to 2.5 ms (180°)
    min_duty = 1000    # ~0.5 ms
    max_duty = 9000    # ~2.5 ms
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    print(f"Setting angle to {angle}°, duty: {duty}, pulse width: {(duty/65535)*20}ms")
    servo.duty_u16(duty)

# Example movement
while True:
    for angle in range(0, 181, 1):  # 0° to 180°
        set_angle(angle)
        print(f"Moving to {angle}°")
        print(servo)
        time.sleep(0.05)
        led.toggle()
    for angle in range(180, -1, -1):  # 180° back to 0°
        led.toggle()
        print(f"Moving to {angle}°")
        set_angle(angle)
        time.sleep(0.05)

serv01 = Servo_MA(pwm_pin=16, min_us=500, max_us=2500, freq=50)
servo1.pwm.duty_u16(5000)
time.sleep(5)
servo1.pwm.duty_u16(2000)