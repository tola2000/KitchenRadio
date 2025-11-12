from luma.core.interface.parallel import parallel
from luma.oled.device import ssd1322
from PIL import ImageDraw

# Define GPIO pins
interface = parallel(
	data_pins=[4, 17, 27, 22, 5, 6, 13, 19],
	cs=26,
	wr=20,
	dc=21,
	rst=16
)

device = ssd1322(interface)
device.clear()

draw = ImageDraw.Draw(device)
draw.text((10, 10), "SSD1322 Ready!", fill="white")
device.show()
