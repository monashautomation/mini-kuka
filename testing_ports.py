import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    print(f"Port: {port.device}, Description: {port.description}, HWID: {port.hwid}")
