from pico_usb_serial import serial

# Simple output
serial.println("Hello, World!")
serial.printf("Value: %d\n", 42)

# Reading input

while True:
    if serial.available():
        line = serial.read_line(timeout=0.1)
        serial.println(f"You entered: {line}")



