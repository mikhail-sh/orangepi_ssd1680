from ssd1680 import SSD1680

ssd = SSD1680(8,7,5,frequency=20000000)	#dc, res, busy

ssd.clear()
ssd.show_string("Hello World!",0, 5, multiplier=2)
ssd.display()

