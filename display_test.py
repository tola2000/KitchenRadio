import RPi.GPIO as GPIO
import time

# Pin definitions
DATA_PINS = [4, 17, 27, 22, 5, 6, 13, 19]  # D0-D7
CS, WR, DC, RESET = 26, 20, 21, 16

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in DATA_PINS + [CS, WR, DC, RESET]:
	GPIO.setup(pin, GPIO.OUT)

# Reset display
GPIO.output(RESET, GPIO.LOW)
time.sleep(0.1)
GPIO.output(RESET, GPIO.HIGH)

def write_byte(value, is_data=True):
	GPIO.output(DC, GPIO.HIGH if is_data else GPIO.LOW)
	for i, pin in enumerate(DATA_PINS):
    	GPIO.output(pin, (value >> i) & 1)
	GPIO.output(CS, GPIO.LOW)
	GPIO.output(WR, GPIO.LOW)
	GPIO.output(WR, GPIO.HIGH)
	GPIO.output(CS, GPIO.HIGH)

# Send command
def send_cmd(cmd):
	write_byte(cmd, is_data=False)

# Send data
def send_data(data):
	write_byte(data, is_data=True)

# SSD1322 Initialization (basic)
def init_ssd1322():
	send_cmd(0xFD)  # Unlock command
	send_data(0x12)
	send_cmd(0xAE)  # Display OFF
	send_cmd(0xB3)  # Clock divider
	send_data(0x91)
	send_cmd(0xCA)  # Set multiplex ratio
	send_data(0x3F)
	send_cmd(0xA0)  # Set remap
	send_data(0x14)
	send_cmd(0xA1)  # Set display start line
	send_data(0x00)
	send_cmd(0xA2)  # Set display offset
	send_data(0x00)
	send_cmd(0xAB)  # Enable internal VDD regulator
	send_data(0x01)
	send_cmd(0xAF)  # Display ON

# Test
init_ssd1322()
print("SSD1322 initialized!")
