import sys
import select
import time
import gc
from machine import Timer

class PicoUSBSerial:
    """
    USB Serial interface class for Raspberry Pi Pico with MicroPython
    Provides enhanced functionality for USB communication
    """
    
    def __init__(self, timeout=1.0, buffer_size=1024):
        """
        Initialize the USB Serial interface
        
        Args:
            timeout (float): Default timeout for operations in seconds
            buffer_size (int): Size of internal read buffer
        """
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.rx_buffer = []
        self.rx_callback = None
        self.echo_mode = False
        self.line_ending = '\r\n'
        self._poller = select.poll()
        self._poller.register(sys.stdin, select.POLLIN)
        
    def available(self):
        """
        Check how many characters are available to read
        
        Returns:
            int: Number of characters in buffer
        """
        # Check for new data
        self._update_buffer()
        return len(self.rx_buffer)
    
    def _update_buffer(self):
        """Internal method to update the receive buffer"""
        if self._poller.poll(0):  # 0 = non-blocking
            try:
                char = sys.stdin.read(1)
                if char:
                    self.rx_buffer.extend(char)
                    if len(self.rx_buffer) > self.buffer_size:
                        self.rx_buffer = self.rx_buffer[-self.buffer_size:]
            except:
                pass
    
    def read(self, num_chars=1):
        """
        Read specified number of characters
        
        Args:
            num_chars (int): Number of characters to read
            
        Returns:
            str: Read characters or empty string if none available
        """
        self._update_buffer()
        
        if len(self.rx_buffer) >= num_chars:
            result = ''.join(self.rx_buffer[:num_chars])
            self.rx_buffer = self.rx_buffer[num_chars:]
            return result
        return ''
    
    def read_timeout(self, num_chars=1, timeout=None):
        """
        Read with timeout
        
        Args:
            num_chars (int): Number of characters to read
            timeout (float): Timeout in seconds (uses default if None)
            
        Returns:
            str: Read characters or empty string if timeout
        """
        if timeout is None:
            timeout = self.timeout
            
        start_time = time.ticks_ms()
        timeout_ms = int(timeout * 1000)
        
        while len(self.rx_buffer) < num_chars:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                break
            self._update_buffer()
            time.sleep_ms(1)
        
        return self.read(min(num_chars, len(self.rx_buffer)))
    
    def read_line(self, timeout=None):
        """
        Read a complete line (until newline)
        
        Args:
            timeout (float): Timeout in seconds
            
        Returns:
            str: Complete line without line ending
        """
        if timeout is None:
            timeout = self.timeout
            
        line = ""
        start_time = time.ticks_ms()
        timeout_ms = int(timeout * 1000)
        
        while True:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                break
                
            self._update_buffer()
            
            if self.rx_buffer:
                char = self.rx_buffer.pop(0)
                if char in '\r\n':
                    if line:  # Don't return empty lines from just newlines
                        break
                else:
                    line += char
            else:
                time.sleep_ms(1)
        
        return line
    
    def read_all(self):
        """
        Read all available characters
        
        Returns:
            str: All available characters
        """
        self._update_buffer()
        result = ''.join(self.rx_buffer)
        self.rx_buffer.clear()
        return result
    
    def read_bytes(self, num_bytes, timeout=None):
        """
        Read specified number of bytes
        
        Args:
            num_bytes (int): Number of bytes to read
            timeout (float): Timeout in seconds
            
        Returns:
            bytes: Read bytes
        """
        data = self.read_timeout(num_bytes, timeout)
        return data.encode('utf-8') if data else b''
    
    def write(self, data):
        """
        Write data to USB serial
        
        Args:
            data: Data to write (str, bytes, or int)
        """
        if isinstance(data, int):
            data = chr(data)
        elif isinstance(data, bytes):
            data = data.decode('utf-8')
        
        sys.stdout.write(data)
        
        if self.echo_mode and self.rx_callback:
            self.rx_callback(data)
    
    def write_bytes(self, data):
        """
        Write bytes to USB serial
        
        Args:
            data (bytes): Bytes to write
        """
        if isinstance(data, (list, tuple)):
            data = bytes(data)
        self.write(data)
    
    def print(self, *args, sep=' ', end=''):
        """
        Print with custom separator and ending
        
        Args:
            *args: Arguments to print
            sep (str): Separator between arguments
            end (str): String appended after the last argument
        """
        output = sep.join(str(arg) for arg in args) + end
        self.write(output)
    
    def println(self, *args, sep=' '):
        """
        Print with newline
        
        Args:
            *args: Arguments to print
            sep (str): Separator between arguments
        """
        self.print(*args, sep=sep, end=self.line_ending)
    
    def printf(self, format_string, *args):
        """
        Formatted print
        
        Args:
            format_string (str): Format string
            *args: Arguments for formatting
        """
        try:
            output = format_string % args
            self.write(output)
        except:
            self.write(format_string)
    
    def flush(self):
        """Flush output buffer"""
        try:
            sys.stdout.flush()
        except:
            pass
    
    def clear_input(self):
        """Clear the input buffer"""
        self.rx_buffer.clear()
        # Consume any pending input
        while self._poller.poll(0):
            try:
                sys.stdin.read(1)
            except:
                break
    
    def set_line_ending(self, ending):
        """
        Set line ending style
        
        Args:
            ending (str): Line ending ('\n', '\r\n', etc.)
        """
        self.line_ending = ending
    
    def set_timeout(self, timeout):
        """
        Set default timeout
        
        Args:
            timeout (float): Timeout in seconds
        """
        self.timeout = timeout
    
    def set_rx_callback(self, callback):
        """
        Set callback function for received data
        
        Args:
            callback (function): Function to call with received data
        """
        self.rx_callback = callback
    
    def enable_echo(self, enable=True):
        """
        Enable/disable echo mode
        
        Args:
            enable (bool): True to enable echo
        """
        self.echo_mode = enable
    
    def wait_for_input(self, timeout=None):
        """
        Wait for input to become available
        
        Args:
            timeout (float): Timeout in seconds
            
        Returns:
            bool: True if input is available
        """
        if timeout is None:
            timeout = self.timeout
            
        timeout_ms = int(timeout * 1000)
        return bool(self._poller.poll(timeout_ms))
    
    def readline_interactive(self, prompt=""):
        """
        Interactive readline with prompt
        
        Args:
            prompt (str): Prompt to display
            
        Returns:
            str: Input line
        """
        if prompt:
            self.write(prompt)
            self.flush()
        
        line = ""
        while True:
            if self.wait_for_input(0.1):
                char = self.read(1)
                if char:
                    if char in '\r\n':
                        self.println()
                        break
                    elif char == '\b' or ord(char) == 127:  # Backspace/Delete
                        if line:
                            line = line[:-1]
                            self.write('\b \b')  # Erase character
                    else:
                        line += char
                        self.write(char)  # Echo character
        
        return line
    
    def send_command(self, command, wait_response=True, timeout=None):
        """
        Send command and optionally wait for response
        
        Args:
            command (str): Command to send
            wait_response (bool): Whether to wait for response
            timeout (float): Timeout for response
            
        Returns:
            str: Response if wait_response is True
        """
        self.println(command)
        self.flush()
        
        if wait_response:
            return self.read_line(timeout)
        return ""
    
    def process_callbacks(self):
        """
        Process any pending callbacks (call in main loop)
        """
        if self.rx_callback and self.available():
            data = self.read_all()
            if data:
                self.rx_callback(data)


# Example usage and utilities
class SerialProtocol:
    """Simple protocol handler for structured communication"""
    
    def __init__(self, serial, delimiter='|', terminator='\n'):
        self.serial = serial
        self.delimiter = delimiter
        self.terminator = terminator
    
    def send_message(self, msg_type, data):
        """Send structured message"""
        message = f"{msg_type}{self.delimiter}{data}{self.terminator}"
        self.serial.write(message)
    
    def parse_message(self, raw_message):
        """Parse received structured message"""
        if self.delimiter in raw_message:
            parts = raw_message.strip().split(self.delimiter, 1)
            return parts[0], parts[1] if len(parts) > 1 else ""
        return raw_message.strip(), ""


# Example usage functions
def basic_example():
    """Basic USB serial communication example"""
    serial = PicoUSBSerial()
    
    serial.println("Pico USB Serial Ready!")
    serial.printf("System started at: %d\n", time.ticks_ms())
    
    while True:
        if serial.available():
            data = serial.read_line(timeout=1.0)
            if data:
                serial.printf("You said: '%s'\n", data)
                
                # Echo commands
                if data.lower() == 'hello':
                    serial.println("Hello back!")
                elif data.lower() == 'time':
                    serial.printf("Current time: %d ms\n", time.ticks_ms())
                elif data.lower() == 'mem':
                    gc.collect()
                    serial.printf("Free memory: %d bytes\n", gc.mem_free())
                elif data.lower() == 'exit':
                    serial.println("Goodbye!")
                    break
        
        time.sleep_ms(10)

def callback_example():
    """Example using callbacks for received data"""
    serial = PicoUSBSerial()
    
    def on_data_received(data):
        serial.printf("Callback received: '%s'\n", data)
        if 'led' in data.lower():
            # Toggle LED or perform action
            serial.println("LED command processed")
    
    serial.set_rx_callback(on_data_received)
    serial.println("Callback example ready")
    
    while True:
        serial.process_callbacks()
        time.sleep_ms(50)

def interactive_example():
    """Interactive menu example"""
    serial = PicoUSBSerial()
    
    def show_menu():
        serial.println("\n=== Pico Menu ===")
        serial.println("1. System Info")
        serial.println("2. Memory Status") 
        serial.println("3. Echo Test")
        serial.println("4. Exit")
        serial.print("Choice: ")
    
    while True:
        show_menu()
        choice = serial.readline_interactive().strip()
        
        if choice == '1':
            serial.printf("MicroPython: %s\n", sys.version)
            serial.printf("Platform: %s\n", sys.platform)
        elif choice == '2':
            gc.collect()
            serial.printf("Free memory: %d bytes\n", gc.mem_free())
        elif choice == '3':
            serial.println("Enter text to echo (empty line to stop):")
            while True:
                text = serial.readline_interactive("> ")
                if not text:
                    break
                serial.printf("Echo: %s\n", text)
        elif choice == '4':
            serial.println("Goodbye!")
            break
        else:
            serial.println("Invalid choice!")

def protocol_example():
    """Example using structured protocol"""
    serial = PicoUSBSerial()
    protocol = SerialProtocol(serial)
    
    protocol.send_message("STATUS", "System Ready")
    
    while True:
        if serial.available():
            raw_msg = serial.read_line()
            if raw_msg:
                msg_type, data = protocol.parse_message(raw_msg)
                
                if msg_type == "GET":
                    if data == "time":
                        protocol.send_message("RESPONSE", str(time.ticks_ms()))
                    elif data == "memory":
                        gc.collect()
                        protocol.send_message("RESPONSE", str(gc.mem_free()))
                elif msg_type == "SET":
                    protocol.send_message("ACK", f"Set command: {data}")
        
        time.sleep_ms(10)

# Global instance for easy access
serial = PicoUSBSerial()

# Usage:
# from pico_usb_serial import serial
# serial.println("Hello World!")