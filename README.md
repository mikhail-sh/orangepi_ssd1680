# Python library for SSD1680 OrangePi
Library written in Python to work with SSD1680 on OrangePi (supports partial update, tested on OrangePi Zero2). Added Russian font. 

Based on:
  - [С driver SPI, font, and LUT for partial update](https://github.com/marko-pi/parallel/tree/main)
  - [Working with the framebuffer, text output, etc.](https://github.com/hfwang132/ssd1680-micropython-drivers/blob/main/ssd1680.py)

For use need install [wiringOP-Python](https://github.com/orangepi-xunlong/wiringOP-Python) and copy ```spi.so```, ```ssd1680.py```, ```fonts.py```.

# Using
```python
from ssd1680 import SSD1680
ssd = SSD1680(8,7,5,frequency=20000000)	#dc, res, busy
ssd.clear()
ssd.show_string("Hello World!",0, 5, multiplier=2)
ssd.display()
```
### Partial update
For partial update use function ```display_partial()```, example:
```python
ssd.clear()
ssd.show_string("Partial update",0, 5, multiplier=2)
ssd.display_partial()
```
