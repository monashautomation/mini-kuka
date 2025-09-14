from machine import Pin, PWM
import time

class Servo_MA:
    def __init__(self, pwm_pin, min_us=500, max_us=2500, freq=50):
        """
        Initialize the Servo object.

        :param pwm: PWM object (must have .duty_ns() or .duty_u16() method)
        :param min_us: Minimum pulse width in microseconds
        :param max_us: Maximum pulse width in microseconds
        :param freq: PWM frequency in Hz
        """
        print("CHECKING SERVO INIT")
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(freq)
        self.min_us = min_us
        self.max_us = max_us
        self.freq = freq
        self.current_angle = None  # Initialize current angle
        self.lp_angle = None  # Last position angle

    def angle_to_us(self, angle):
        """
        Convert angle (0-180) to pulse width in microseconds.
        """
        angle = max(0, min(180, angle))
        return int(self.min_us + (self.max_us - self.min_us) * (angle / 180))

    def set_angle(self, angle):
        """
        Set servo to specified angle (0-180 degrees).
        """
        pulse_us = self.angle_to_us(angle)
        period_us = 1_000_000 // self.freq
        duty = int((pulse_us / period_us) * 65535) 
        print(f"Setting angle to {angle}°, pulse width: {pulse_us}us, duty: {duty}")
        self.lp_angle = self.lp_angle * 0.9 + angle * 0.1 if self.lp_angle is not None else angle
        self.current_angle = angle
        self.pwm.duty_u16(duty)
    
    def set_angle_smooth(self, angle,smoothing_factor=0.05):
        """
        Smoothly move the servo to the specified angle.
        """
        if self.current_angle is not None:
            if abs(self.current_angle - angle) > 1:
                temp_angle = self.current_angle*(1-smoothing_factor) + angle*smoothing_factor
                self.set_angle(temp_angle)
                print(f"Smooth moving to {angle}°, current angle: {self.current_angle}°")
            return
        


    def get_angle(self):
        """
        Get the current angle of the servo.
        """
        return self.current_angle if self.current_angle is not None else 0
    
    

class RobotArm:
    def __init__(self, servo_pins):
        self.servos = [Servo_MA(pin) for pin in servo_pins]

    def get_servos(self):
        return self.servos

    def set_joint_angle(self, joint_index, angle):
        if joint_index < 0 or joint_index >= len(self.servos):
            raise IndexError("Invalid joint index")
        self.servos[joint_index].set_angle(angle)

    def get_joint_angle(self, joint_index):
        if joint_index < 0 or joint_index >= len(self.servos):
            raise IndexError("Invalid joint index")
        return self.servos[joint_index].get_angle()

    def set_all_angles(self, angles):
        if len(angles) != len(self.servos):
            raise ValueError("Angles list length does not match number of servos")
        for i, angle in enumerate(angles):
            self.servos[i].set_angle(angle)

    def get_all_angles(self):
        return [servo.get_angle() for servo in self.servos]

# servo1 = Servo_MA(pwm_pin=16, min_us=500, max_us=2500, freq=50)
# while True:
#     servo1.set_angle(0)
#     time.sleep(2)
#     servo1.set_angle(180)
#     time.sleep(2)
