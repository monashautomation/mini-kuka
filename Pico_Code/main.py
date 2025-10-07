from pico_usb_serial import serial
from robot_arm_class import RobotArm,Servo_MA
from time import sleep
import machine

# Configuration: GPIO pins used for each servo. Update these to match your wiring.
# Assumption: using GPIO 0-4 by default. If you use different pins (e.g. 16-20), update here.
# Pins set to user's wiring (GP0, GP1, GP2, GP3, GP5). Update if you change wiring.
SERVO_PINS = [0, 1, 2, 3, 5]

# Create servo objects
servos = [Servo_MA(pwm_pin=pin, min_us=500, max_us=2500, freq=50) for pin in SERVO_PINS]

# State array for angles (initialized to 90 as neutral)
servo_values = [90 for _ in SERVO_PINS]

onboard_led = machine.Pin("LED", machine.Pin.OUT)


def parse_serial_data(data_string):
    """Parse serial data in format 'S1 90,S2 90' or 'S1 90,S2 90\n' and update servo_values.
    Returns the servo_values list (possibly partially updated).
    """
    global servo_values
    try:
        # Clean and normalize input
        data_string = data_string.strip()
        # remove stray carriage returns/newlines
        data_string = data_string.replace('\r', '').replace('\n', '')
        if not data_string:
            return servo_values

        parts = [p.strip() for p in data_string.split(',') if p.strip()]
        print("Received parts:", parts)

        for part in parts:
            # Expect format 'S<number> <angle>' or 'S<number>:<angle>'
            tokens = part.replace(':', ' ').split()
            if len(tokens) >= 2 and tokens[0].upper().startswith('S'):
                try:
                    idx = int(tokens[0][1:]) - 1
                    angle = int(tokens[1])
                    if 0 <= idx < len(servo_values) and 0 <= angle <= 180:
                        servo_values[idx] = angle
                        print(f"Parsed S{idx+1} -> {angle}")
                    else:
                        print(f"Ignoring out-of-range servo/index: S{idx+1} {angle}")
                except ValueError:
                    print("ValueError parsing token:", tokens)
        return servo_values
    except Exception as e:
        print("Error parsing serial data:", e)
        return servo_values


while True:
    if serial.available():
        line = serial.read_line(timeout=0.1)
        if line is None:
            line = ''
        # Echo what was received (useful for debugging via serial terminal)
        serial.println(f"You entered: {line}")
        updated_values = parse_serial_data(line)
        print(f"Updated servo values: {updated_values}")
        # Apply to servos we have instantiated
        try:
            for i, val in enumerate(updated_values):
                if i < len(servos):
                    servos[i].set_angle(val)
            # Optionally echo back a confirmation
            serial.println(f"Set angles: {','.join(str(v) for v in updated_values)}")
        except Exception as e:
            print("Error setting servo angle:", e)

    else:
        sleep(0.1)
        onboard_led.toggle()
        continue




