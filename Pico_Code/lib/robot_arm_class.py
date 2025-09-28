from machine import Pin, PWM
import time

class Servo_MA:
    """
    Servo control class supporting both 180° and 360° servos (like MG90).
    
    Usage Examples:
    # 180° servo (default)
    servo_180 = Servo_MA(pwm_pin=5)
    servo_180.set_angle(90)  # Set to 90 degrees
    
    # 360° servo
    servo_360 = Servo_MA(pwm_pin=6, servo_type="360")
    servo_360.set_angle(270)  # Set to 270 degrees
    
    # MG90 servo (typically 180°)
    mg90 = Servo_MA(pwm_pin=7, min_us=600, max_us=2400, servo_type="180")
    """
    def __init__(self, pwm_pin,joint_number, min_us=500, max_us=2500, freq=50, servo_type="180"):
        """
        Initialize the Servo object.

        :param pwm_pin: PWM pin number
        :param min_us: Minimum pulse width in microseconds
        :param max_us: Maximum pulse width in microseconds
        :param freq: PWM frequency in Hz
        :param servo_type: "180" for 180° servo (default) or "360" for 360° servo
        """
        print("CHECKING SERVO INIT")
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(freq)
        self.min_us = min_us
        self.max_us = max_us
        self.freq = freq
        self.servo_type = servo_type
        self.max_angle = 180 if servo_type == "180" else 360
        self.current_angle = None  # Initialize current angle
        self.lp_angle = None  # Last position angle
        self.at_target = False
        self.joint_number = joint_number
        print(f"Servo initialized: {self.max_angle}° range, PWM pin {pwm_pin}")

    def angle_to_us(self, angle):
        """
        Convert angle to pulse width in microseconds.
        For 180° servo: 0-180 degrees
        For 360° servo: 0-360 degrees
        """
        angle = max(0, min(self.max_angle, angle))
        return int(self.min_us + (self.max_us - self.min_us) * (angle / self.max_angle))

    def set_angle(self, angle):
        """
        Set servo to specified angle.
        Range: 0-180° for 180° servo, 0-360° for 360° servo
        """
        pulse_us = self.angle_to_us(angle)
        period_us = 1_000_000 // self.freq
        duty = int((pulse_us / period_us) * 65535) 
        print(f"Setting angle to {angle}°, pulse width: {pulse_us}us, duty: {duty}")
        self.lp_angle = self.lp_angle * 0.9 + angle * 0.1 if self.lp_angle is not None else angle
        self.current_angle = angle
        self.pwm.duty_u16(duty)
    
    def set_angle_smooth(self, angle, smoothing_factor=0.05):
        """
        Smoothly move the servo to the specified angle.
        """
        if self.current_angle is not None:
            if abs(self.current_angle - angle) > 1:
                temp_angle = self.current_angle*(1-smoothing_factor) + angle*smoothing_factor
                self.set_angle(temp_angle)
                print(f"J{self.joint_number} smoothly moving to {angle}°, current angle: {self.current_angle}°")
                self.at_target = False
            else:
                self.at_target = True
            return

    def get_angle(self):
        """
        Get the current angle of the servo.
        """
        return self.current_angle if self.current_angle is not None else 0
    
    def get_servo_type(self):
        """
        Get the servo type and maximum angle.
        """
        return {'type': self.servo_type, 'max_angle': self.max_angle}
    
    def get_stats(self, print_stats=False):
        """
        Get statistics about the servo's current state.
        
        :param print_stats: If True, prints formatted stats to console
        :return: Dictionary containing servo statistics
        """
        # Calculate current pulse width if angle is set
        current_pulse_us = self.angle_to_us(self.current_angle) if self.current_angle is not None else None
        
        # Calculate current duty cycle
        if self.current_angle is not None and current_pulse_us is not None:
            period_us = 1_000_000 // self.freq
            current_duty_u16 = int((current_pulse_us / period_us) * 65535)
            current_duty_percent = (current_pulse_us / period_us) * 100
        else:
            current_duty_u16 = None
            current_duty_percent = None
        
        stats = {
            'joint_number': f'{self.joint_number}',
            'servo_type': f'{self.max_angle}°',
            'current_angle': self.current_angle,
            'lp_angle': round(self.lp_angle, 2) if self.lp_angle is not None else None,
            'at_target': self.at_target,
            'current_pulse_us': current_pulse_us,
            'current_duty_u16': current_duty_u16,
            'current_duty_percent': round(current_duty_percent, 2) if current_duty_percent is not None else None,
            'min_pulse_us': self.min_us,
            'max_pulse_us': self.max_us,
            'pwm_frequency': self.freq,
            'angle_range': f'0-{self.max_angle}°',
            'pulse_range': f'{self.min_us}-{self.max_us}μs'
        }
        
        if print_stats:
            print(f"\n=== SERVO STATISTICS ({stats['servo_type']}) ===")
            print(f"Current Angle:        {stats['current_angle']}°")
            print(f"Low-pass Angle:       {stats['lp_angle']}°")
            print(f"At Target:            {stats['at_target']}")
            print(f"Current Pulse Width:  {stats['current_pulse_us']}μs")
            print(f"Current Duty (u16):   {stats['current_duty_u16']}")
            print(f"Current Duty (%):     {stats['current_duty_percent']}%")
            print(f"PWM Frequency:        {stats['pwm_frequency']}Hz")
            print(f"Pulse Range:          {stats['pulse_range']}")
            print(f"Angle Range:          {stats['angle_range']}")
            print("========================\n")
        
        return stats


    
    

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


if __name__ == "__main__" :
    servo1 = Servo_MA(pwm_pin=19,joint_number="1", min_us=500, max_us=2500, freq=50,servo_type="180")
    target = 0
    servo1.set_angle(0)
    time.sleep(2)
    while True:
        #print("Servo at target ", servo1.at_target,)
        if target == 0:
            servo1.set_angle_smooth(target,smoothing_factor=0.01)
            if servo1.at_target:
                target = 180
        if target == 180:
            servo1.set_angle_smooth(target,smoothing_factor=0.01)
            if servo1.at_target:
                target = 0
    

