#!/usr/bin/env python

from wiringpi import wiringPiSetup as gpioInitialise
from wiringpi import pinMode as gpioSetMode
from wiringpi import digitalWrite as gpioWrite
from wiringpi import digitalRead as gpioRead
import os, numpy, time
from ctypes import cdll, c_int, c_uint, c_uint32, c_void_p
from math import ceil, sqrt
from fonts import asc2_0806

###### Wrapping C library ######
spi = cdll.LoadLibrary("./spi.so")

PI_INPUT = 0
PI_OUTPUT = 1

spiInitialise = spi.spiInitialise
spiInitialise.argtypes = [c_int, c_uint32]
spiWrite = spi.spiWrite
spiWrite.argtypes = [c_void_p, c_int]


# LUT for a single colour refresh, obtained from WaveShare
lut_black = numpy.array([
0x80,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x40,0x00,0x00,0x00,
0x10,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x20,0x00,0x00,0x00,
0x80,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x40,0x00,0x00,0x00,
0x10,0x66,0x00,0x00,0x00,0x00,0x00,0x00,0x20,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x14,0x08,0x00,0x00,0x00,0x00,0x02,
0x0A,0x0A,0x00,0x0A,0x0A,0x00,0x01,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x14,0x08,0x00,0x01,0x00,0x00,0x01,
0x00,0x00,0x00,0x00,0x00,0x00,0x01,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x44,0x44,0x44,0x44,0x44,0x44,0x00,0x00,0x00], dtype = 'uint8')

# LUT for a fast partial refresh
lut_partial = numpy.array([
0x00,0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x80,0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x40,0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x80,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x0A,0x00,0x00,0x00,0x00,0x00,0x02,
0x01,0x00,0x00,0x00,0x00,0x00,0x00,
0x01,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x00,0x00,0x00,0x00,0x00,0x00,0x00,
0x22,0x22,0x22,0x22,0x22,0x22,0x00,0x00,0x00], dtype = 'uint8')


class Color():
    BLACK = 0x00
    WHITE = 0xff
    
class Rotate():
    ROTATE_0 = 0
    ROTATE_90 = 1
    ROTATE_180 = 2
    ROTATE_270 = 3

class Screen():
    def __init__(self, width=128, height=296):
        self.width = width
        self.height = height
        self.width_bytes = ceil(width / 8)
        self.height_bytes = height
        
    def __repr__(self):
        print("screen width: %d" % self.screen.width)
        print("screen height: %d" % self.screen.height)
        print("screen width bytes: %d" % self.screen.width_bytes)
        print("screen height bytes: %d" % self.screen.height_bytes)

class Paint():
    def __init__(self, screen=Screen(), rotate=Rotate.ROTATE_90, bg_color=Color.WHITE):
        self.screen = screen
        self.img = bytearray(self.screen.width_bytes * self.screen.height_bytes)
        self.rotate = rotate
        self.bg_color = bg_color
        
        if self.rotate == Rotate.ROTATE_0 or self.rotate == Rotate.ROTATE_180:
            self.width = self.screen.width
            self.height = self.screen.height
        else:
            self.width = self.screen.height
            self.height = self.screen.width
        
    def __repr__(self):
        self.screen.__repr__()
        print("rotate: %d" % self.rotate)
        print("background color: 0x%x" % self.bg_color)
            
    def fill(self, color):
        self.bg_color = color
        for y in range(self.screen.height_bytes):
            for x in range(self.screen.width_bytes):
                addr = x + y * self.screen.width_bytes
                self.img[addr] = self.bg_color
    
    def _convert_coor(self, x_pos, y_pos, start_from_one=True):
        if self.rotate == Rotate.ROTATE_0:
            x = x_pos
            y = y_pos
        elif self.rotate == Rotate.ROTATE_90:
            x = self.screen.width - y_pos - 1
            y = x_pos
        elif self.rotate == Rotate.ROTATE_180:
            x = self.screen.width - x_pos - 1
            y = self.screen.height - y_pos - 1
        else:
            x = y_pos
            y = self.screen.height - x_pos - 1
            
        if start_from_one:
            x = x - 1
            y = y - 1
            
        return x, y
    
    def draw_point(self, x_pos, y_pos, start_from_one=True):
        x, y = self._convert_coor(x_pos, y_pos)
        if x > self.screen.width or y > self.screen.height or x < 0 or y < 0:
            return
        
        addr = x // 8 + y * self.screen.width_bytes
        raw = self.img[addr]
        
        if (self.bg_color == Color.WHITE):
            self.img[addr] = raw & ~(0x80 >> (x % 8))
        else:
            self.img[addr] = raw | (0x80 >> (x % 8))
            
    def draw_line(self, x_start, y_start, x_end, y_end):
        dx = x_end - x_start
        dy = y_end - y_start
        points = []
        if abs(dx) > abs(dy):
            x_inc = (dx > 0) - (dx < 0)
            x_offset = 0
            for _ in range(abs(dx) + 1):
                x_tmp = x_start + x_offset
                y_tmp = y_start + round(dy / dx * x_offset)
                points.append((x_tmp, y_tmp))
                x_offset = x_offset + x_inc
        else:
            y_inc = (dy > 0) - (dy < 0)
            y_offset = 0
            for _ in range(abs(dy) + 1):
                y_tmp = y_start + y_offset
                x_tmp = x_start + round(dx / dy * y_offset)
                points.append((x_tmp, y_tmp))
                y_offset = y_offset + y_inc
                
        for point in points:
            self.draw_point(point[0], point[1])
            
    def draw_rectangle(self, x_start, y_start, x_end, y_end):
        self.draw_line(x_start, y_start, x_start, y_end)
        self.draw_line(x_start, y_start, x_end, y_start)
        self.draw_line(x_start, y_end, x_end, y_end)
        self.draw_line(x_end, y_start, x_end, y_end)

    def draw_circle(self, x_center, y_center, radius):
        points = []
        for x in range(x_center - radius, x_center + radius):
            y = y_center + round(sqrt(radius ** 2 - (x - x_center) ** 2))
            points.append((x, y))
            y = y_center - round(sqrt(radius ** 2 - (x - x_center) ** 2))
            points.append((x, y))
        for y in range(y_center - radius, y_center + radius):
            x = x_center + round(sqrt(radius ** 2 - (y - y_center) ** 2))
            points.append((x, y))
            x = x_center - round(sqrt(radius ** 2 - (y - y_center) ** 2))
            points.append((x, y))
        
        for point in points:
            self.draw_point(point[0], point[1])
            
    def show_char(self, char, x_start, y_start, font=asc2_0806, font_size=(6, 8), multiplier=1):
        tmp = 0x00
        if ord(char) > 200:
            char_idx = ord(char) - 948
        else: 
            char_idx = ord(char) - 32
        if multiplier == 1:
            for x_offset in range(font_size[0]):
                tmp = font[char_idx][x_offset]
                for y_offset in range(font_size[1]):
                    if tmp & 0x01:
                        self.draw_point(x_start + x_offset, y_start + y_offset)
                    tmp = tmp >> 1
        else:
            for x_offset in range(font_size[0] * multiplier):
                tmp = font[char_idx][x_offset // multiplier]
                for y_offset in range(font_size[1] * multiplier):
                    if tmp & 0x01:
                        self.draw_point(x_start + x_offset, y_start + y_offset)
                    if y_offset % multiplier == multiplier - 1:
                        tmp = tmp >> 1
                
    def show_string(self, string, x_start, y_start, font=asc2_0806, font_size=(6, 8),multiplier=1):
        for idx, char in enumerate(string):
            self.show_char(char, x_start + idx * font_size[0] * multiplier, y_start, font, font_size, multiplier)
            
    def show_bitmap(self, bitmap, x_start, y_start, multiplier=1):
        if multiplier == 1:
            for r, row in enumerate(bitmap):
                for c, col in enumerate(row):
                    if col == 1:
                        self.draw_point(x_start + c, y_start + r)
        else:
            for r in range(len(bitmap) * multiplier):
                for c in range(len(bitmap[0] * multiplier)):
                    if bitmap[r//multiplier][c//multiplier] == 1:
                        self.draw_point(x_start + c, y_start + r)
    
    def show_img(self, img_path, x_start, y_start):
        raise NotImplementedError


##### SSD1680 FUNCTIONS #####
class SSD1680(object):
    def __init__(self, dc, res, busy, dev=1, frequency=20000000):
        self._dc  = dc
        self._res = res
        self._busy = busy

        self.screen = Screen()
        self.paint = Paint(self.screen, rotate=Rotate.ROTATE_90, bg_color=Color.WHITE)

        # Initialise GPIO
        gpioInitialise()
        gpioSetMode(dc, PI_OUTPUT)
        gpioSetMode(res, PI_OUTPUT)
        gpioSetMode(busy, PI_INPUT)

        # Initialise SPI
        spiInitialise(dev, frequency)

        # define buffers for white (negative black) and red pixels
        self.white = numpy.full(4736, 0xff, dtype='uint8')

        # chip reset
        gpioWrite(dc,1)

        gpioWrite(res,1)
        time.sleep(0.05)
        gpioWrite(res,0)
        time.sleep(0.05)
        gpioWrite(res,1)
        while(gpioRead(busy)==1): time.sleep(0.001)

        self.command(0x01,[0x27,0x01,0x01])      # Driver output control (default 0x270100)
        self.command(0x3C,[0x05])                # BorderWavefrom (default 0xC0)
        self.command(0x21,[0x00,0x80])           # Display update control
        self.command(0x18,[0x80])                # Read built-in temperature sensor

        self.command(0x11,[0x01])                # Address mode
        #self.command(0x11,[0x03])                # Address mode: top to bottom, left to right
        self.command(0x44,[0x00,0x0F])           # X address range
        self.command(0x45,[0x27,0x01,0x00,0x00]) # Y address range
        #self.command(0x45,[0x00,0x00,0x27,0x01]) # Y address range
        self.command(0x4E,[0x00])                # X address start
        self.command(0x4F,[0x27,0x01])           # Y address start
        #self.command(0x4F,[0x00,0x00])           # Y address start
        
    def command(self, nam, dat=[]):
        gpioWrite(self._dc,0)
        nam=numpy.array([nam], dtype = 'uint8')
        spiWrite(nam.ctypes.data_as(c_void_p),len(nam))
        gpioWrite(self._dc,1)
        if len(dat)>0:
            if(type(dat)!=numpy.ndarray):
                dat=numpy.array(dat, dtype = 'uint8')
            spiWrite(dat.ctypes.data_as(c_void_p),len(dat))
    
    def date(self, dat=[]):
        gpioWrite(self._dc,1)
        if len(dat)>0:
            if(type(dat)!=numpy.ndarray):
                dat=numpy.array(dat, dtype = 'uint8')
            spiWrite(dat.ctypes.data_as(c_void_p),len(dat))

    def display(self):
        self.command(0x24,self.paint.img[0:4000])            # load negative black picture
        self.date(self.paint.img[4000:4736])
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x32,lut_black)             # Load user-defined LUT for black-only display
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x22,[0xF7])                # Sequence: display
        self.command(0x20)                       # Activate Display Update Sequence
        while(gpioRead(self._busy)==1): time.sleep(0.001)


    def display_black(self):
        self.command(0x24,self.paint.img[0:4000])            # load negative black picture
        self.date(self.paint.img[4000:4736])
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x32,lut_black)             # Load user-defined LUT for black-only display
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x22,[0xC7])                # Sequence: display
        self.command(0x20)                       # Activate Display Update Sequence
        while(gpioRead(self._busy)==1): time.sleep(0.001)

    def display_partial(self):
        self.command(0x24,self.paint.img[0:4000])            # load negative black picture
        self.date(self.paint.img[4000:4736])
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x32,lut_partial)           # Load user-defined LUT for partial refresh
        while(gpioRead(self._busy)==1): time.sleep(0.001)
        self.command(0x22,[0xCC])                # Sequence: display
        self.command(0x20)                       # Activate Display Update Sequence
        while(gpioRead(self._busy)==1): time.sleep(0.001)

    def sleep(self):
        self.command(0x10,[0x01])                # Deep sleep mode

    def close(self):
        pass


    def fill(self, *args, **kwargs):
        self.paint.fill(*args, **kwargs)

    def clear(self):
        self.paint.fill(0xff)
        
    def draw_point(self, *args, **kwargs):
        self.paint.draw_point(*args, **kwargs)
        
    def draw_line(self, *args, **kwargs):
        self.paint.draw_line(*args, **kwargs)
    
    def draw_rectangle(self, *args, **kwargs):
        self.paint.draw_rectangle(*args, **kwargs)
        
    def draw_circle(self, *args, **kwargs):
        self.paint.draw_circle(*args, **kwargs)
        
    def show_char(self, *args, **kwargs):
        self.paint.show_char(*args, **kwargs)
        
    def show_string(self, *args, **kwargs):
        self.paint.show_string(*args, **kwargs)
    
    def show_bitmap(self, *args, **kwargs):
        self.paint.show_bitmap(*args, **kwargs)
        
    def show_img(self, *args, **kwargs):
        self.paint.show_img(*args, **kwargs)