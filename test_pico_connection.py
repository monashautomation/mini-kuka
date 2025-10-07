import serial
import serial.tools.list_ports

def find_pico():
    """
    Check if a Raspberry Pi Pico is connected via serial.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Pico" in port.description or "RP2" in port.description:
            print(f"Pico found on port: {port.device}")
            return port.device
    print("No Pico detected. Make sure it is connected.")
    return None

def test_pico_connection(port):
    """
    Test communication with the Pico by opening the serial port.

    :param port: The COM port where the Pico is connected.
    """
    try:
        with serial.Serial(port, baudrate=9600, timeout=2) as ser:
            print(f"Testing connection on {port}...")
            ser.write(b"PING\n")  # Send a test command
            response = ser.readline().decode().strip()
            if response == "PONG":
                print("Pico responded successfully!")
            else:
                print(f"Unexpected response: {response}")
    except Exception as e:
        print(f"Failed to communicate with device on {port}: {e}")

if __name__ == "__main__":
    test_pico_connection("COM3")