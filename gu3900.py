"""
User mode device driver for Noritake GU3900-series Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time

# thank god for code folding
_opcode = {
# control codes
    'back_space'      : '\x08',
    'horizontal_tab'  : '\x09',
    'line_feed'       : '\x0A',
    'home_position'   : '\x0B',
    'carriage_return' : '\x0D',
    'clear_screen'    : '\x0C',
# general setting commands
    'brightness_level' : '\x1F\x58', # see docs
    'init_display'     : '\x1B\x40',
    'move_cursor'      : '\x1F\x24', # see docs
    'show_cursor'      : '\x1F\x43', # *00h off, 01h on
# character display setting commands
    'write_screen_mode'  : '\x1F\x28\x77\x10', # *00h display screen mode, 01h all screen mode
    'intl_font'          : '\x1B\x52', # *00h USA, see docs
    'char_code_type'     : '\x1B\x74', # *00h PC437, see docs
    'overwrite_mode'     : '\x1F\x01',
    'vscroll_mode'       : '\x1F\x02',
    'hscroll_mode'       : '\x1F\x03',
    'hscroll_speed'      : '\x1F\x73',
    'font_size'          : '\x1F\x28\x67\x01', # *01h 6x8, 02h 8x16, 04h 16x32
    'two_byte_char_mode' : '\x1F\x28\x67\x02', # *00h one byte, 01h two byte
    'two_byte_char_type' : '\x1F\x28\x67\x03', # *00h japan, 01h korea, 02h simp china, 03h trad china
    'font_mag_display'   : '\x1F\x28\x67\x40', # *01h,01h x,y magnification
    'char_bold_display'  : '\x1F\x28\x67\x41', # *00h off, 01h on
# display action setting commands
    'wait'                   : '\x1F\x28\x61\x01', # t * 0.5s
    'short_wait'             : '\x1F\x28\x61\x02', # t * 14ms
    'scroll_display_action'  : '\x1F\x28\x61\x10', # see docs
    'display_blink'          : '\x1F\x28\x61\x11', # see docs
    'curtain_display_action' : '\x1F\x28\x61\x12', # see docs
    'spring_display_action'  : '\x1F\x28\x61\x13', # see docs
    'random_display_action'  : '\x1F\x28\x61\x14', # see docs
    'display_power'          : '\x1F\x28\x61\x40', # see docs
# bit image display setting commands
    'draw_dot_pattern'      : '\x1F\x28\x64\x10', # see docs
    'draw_line_box_ptrn'    : '\x1F\x28\x64\x11', # see docs
    'display_rt_bit_image'  : '\x1F\x28\x66\x11', # see docs
    'define_ram_bit_image'  : '\x1F\x28\x66\x01', # see docs
    'define_from_bit_image' : '\x1F\x28\x65\x10', # see docs
    'display_dl_bit_image'  : '\x1F\x28\x66\x10', # see docs
    'scroll_dl_bit_image'   : '\x1F\x28\x66\x90', # see docs
# general display setting commands
    'hscroll_display_quality' : '\x1f\x6d', # *00h favor scroll speed, 01h favor visual quality
    'reverse_display' : '\x1F\x72', # *00h off, 01h on
    'write_mix_mode'  : '\x1F\x77', # *00h over, 01h or, 02h and, 03h xor
# window display setting commands
    'select_current_window' : '\x1F\x28\x77\x01', # 00h base, 01h window 1, 02h w2, 03h w3, 04h w4
    'define_user_window'    : '\x1f\x28\x77\x02', # see docs
# download character setting commands
# user setup mode setting commands
# gpio port control commands
# macro setting commands
    'define_ram_macro'  : '\x1F\x3A',
    'define_from_macro' : '\x1F\x28\x65\x12',
    'execute_macro'     : '\x1F\x5E'
# other setting commands
}

def _makearg(*args):
    return ''.join([chr(a) for a in args])

ONE_USEC = 0.000001

class GU3900(object):
    
# properties
    def setBold(self, value):
        assert value in [0,1] 
        self._bold = value
        self._char_bold_display(chr(value))
                
    bold = property(lambda self:self._bold, setBold)
    
    def setFontSize(self, value):
        assert value in [1, 2, 4]
        self._fontSize = value
        self._font_size(chr(value))
        
    fontSize = property(lambda self:self._fontSize, setFontSize)
    
    def setBrightness(self, value):
        assert 0 <= value <= 100
        self._brightness = value
        arg = 0x10 + value * 2 / 25
        self._brightness_level(chr(arg))
        
    brightness = property(lambda self:self._brightness, setBrightness)
    
    def setPower(self, value):
        assert value in [0,1]
        self._power = value
        self._display_power(chr(value))
    power = property(lambda self:self._power, setPower)
    
    def setReverse(self, value):
        assert value in [0,1]
        self._reverse = value
        self._reverse_display(chr(value))
    reverse = property(lambda self:self._reverse, setReverse)
    
    def selectWindow(self, value):
        assert value in [0,1,2,3,4]
        self._select_current_window(chr(value))
        
    def setWriteMode(self,value):
        self._write_mix_mode(chr(value))
    writeMode = property(fset=setWriteMode)
    
    TAB  = property(lambda self: _opcode['horizontal_tab'])
    BS   = property(lambda self: _opcode['back_space'])
    LF   = property(lambda self: _opcode['line_feed'])
    HOME = property(lambda self: _opcode['home_position'])
    CR   = property(lambda self: _opcode['carriage_return'])
    CLR  = property(lambda self: _opcode['clear_screen'])
    
# commands
    def init(self):
        self._init_display()
        self.writeMode = 0
        
    def clear(self):
        self._clear_screen()
        
    def showCursor(self, value=True):
        self._show_cursor(chr(value))
        
    def moveCursor(self, x, y):
        assert 0<=x<=511
        assert 0<=y<=7
        self._move_cursor(_makearg(x%256, x/256, y, 0))
        
    def magnifyFont(self, x=1, y=1):
        assert x in [1,2,3,4]
        assert y in [1,2,3,4]
        self._font_mag_display(_makearg(x, y))
        

    def wait(self, interval):
        self._wait(chr(interval))
        
    def drawPoint(self, x, y, pen=1):
        assert 0 <= x < 256
        assert 0 <= y < 64
        self._draw_dot_pattern(_makearg(pen, x, 0, y, 0))
        
    def defineWindow(self, window, x, y, w, h):
        assert window in [1,2,3,4]
        assert isinstance(x, int) and 0<=x<=511
        assert isinstance(y, int) and 0<=y<=7
        assert isinstance(w, int) and 1<=w<=512
        assert isinstance(h, int) and 1<=h<=8
        self._define_user_window(_makearg(window,1,x%256,x/256,y,0,w%256,w/256,h,0))
    
    def cancelWindow(self, window):
        assert window in [1,2,3,4]
        self._define_user_window(_makearg(window,0,0,0,0,0,0,0,0,0))
        
    def drawLine(self, x1, y1, x2, y2, pen=1):
        self._draw_line_box_ptrn(_makearg(0, pen, x1, 0, y1, 0, x2, 0, y2, 0))
    
    def drawRect(self, x1, y1, x2, y2, pen=1):
        self._draw_line_box_ptrn(_makearg(1, pen, x1, 0, y1, 0, x2, 0, y2, 0))
    
    def fillRect(self, x1, y1, x2, y2, pen=1):
        self._draw_line_box_ptrn(_makearg(2, pen, x1, 0, y1, 0, x2, 0, y2, 0))
        
    def drawImage(self, x, y, w, h, image):
        self.moveCursor(x,y)
        self._display_rt_bit_image(_makearg(w%256, w/256, h%256, h/256, 1) + image)
        
    def writeRamImage(self, address, image):
        length = len(image)
        arg = _makearg(address%256, address/256, 0, length%256, length/256, 0) + image
        self._define_ram_bit_image(arg)
        
    def copyImage(self, address, srcH, dstW, dstH):
        opcode = '\x1F\x28\x66\x10'
        arg = '\x02%s%s\x00%s\x00%s%s%s\x00\x01' % \
                    (chr(address%256), chr(address/256), chr(srcH),
                     chr(dstW%256), chr(dstW/256), chr(dstH) )
        self.write(opcode + arg)

    def copyRamImage(self, address, srcH, dstW, dstH):
        opcode = '\x1F\x28\x66\x10'
        arg = '\x00%s%s\x00%s\x00%s%s%s\x00\x01' % \
                    (chr(address%256), chr(address/256), chr(srcH),
                     chr(dstW%256), chr(dstW/256), chr(dstH) )
        self.write(opcode + arg)

# private
    # generate private functions for all opcodes in table
    for op in _opcode.keys():
        exec "def _%s(self, arg=''):\n\
            \"Send the '%s' opcode to the display\"\n\
            self.write(_opcode['%s'] + arg)" % (op, op, op)
    

try:
    
    import serial # http://pyserial.sourceforge.net
    
    class GU3900Ser(GU3900):
    
        def __init__(self, W=256, H=64, device='/dev/ttyS0', speed=38400):
            
            self._ser = serial.Serial(device, speed, writeTimeout=2, dsrdtr=True )
            self._ser.open()
            self.init()
            self._power = 1
            self._bold = False
            self._brightness = 100
            self._fontSize = 1
            self._reverse = 0
            
            self.W = W
            self.H = H
            
        def write(self, str):
            self._ser.write(str)    

except: print 'GU3900 serial not available'    

try:

    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class GU3900Par(GU3900):
        
        def __init__(self, W=256, H=64, dev=0):
            
            p = parallel.Parallel(dev)
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.getRDY  = p.getInBusy     # pin 11
            
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            self.H = H
            
            # enable the fast write if using the default wiring and the C library is installed
            try:
                assert self.setWR == p.setDataStrobe
                assert self.getRDY == p.getInBusy
                from ctypes import cdll
                from sys import prefix
                self._pydisplay = cdll.LoadLibrary(prefix + '/lib/python/site-packages/_pydisplay.so')
                self.write = self.fastWrite
                self.fd = p._fd
                print 'gu3900: using fast I/O library'
            except:
                self.write = self.slowWrite
                print 'gu3900: fast I/O library not available, using pyparallel'
                
            self.init()
            
        def slowWrite(self, s):
            for c in s:
                self.setData(ord(c)) # set the data bits
                while not self.getRDY(): pass
                self.setWR(1)        # toggle display /WR pin to signal a write
                self.setWR(0)
    
        def fastWrite(self, data):
            self._pydisplay.gu3900_write(self.fd, data, len(data))                

except: print 'GU3900 parallel not available'    

try:
    
    import ftdi
    
    # these are tuning parameters
    USB_CHUNK_SIZE = 64
    BAUD_RATE = 0x2800
    
    # this is excruciatingly slow
    class GU3900USB(GU3900):
    
        def __init__(self, W=256, H=64, dev=0):
            
            self.W = W
            self.H = H
            
            device = ftdi.getFtdiDevices()
            self.usb = ftdi.FT232R(device[dev])
            self.usb.setBaudRate(BAUD_RATE)
            self.usb.enableBitBang()
            
            self.init()
            
        def write(self, data):
    
            while len(data) > 0:
                
                try: self.usb.write(data[:USB_CHUNK_SIZE])
                except: pass
                
                data = data[USB_CHUNK_SIZE:]

except: print 'GU3900 FTDI USB not available'        

import random
            
def pong(d, mode=1, n = 100000):
       
    bits = '\xC0\x60\x30\x18\x0C\x06\x03\x01'
    w = 1
    x = 0; y = 0
    dx = dy = 1
    while n:
        
        n -= 1
        
        # update ball position
        if x < 0-dx: dx = random.randint(1,3)
        if x > 255-w-dx: dx = -2
        x = (x+dx)%256
        if y < 0-dy: dy = 1
        if y > 63-w-dy: dy = -1
        y = (y+dy)%64
        
        # draw the ball
        d.writeMode = mode
        d.drawImage(x, y/8, 2, 1, bits[y%8]*2)
        if (y%8 == 7): d.drawImage(x,y/8+1,2,1,'\x80\x80')
        
        # ...and erase the ball
        d.writeMode = 3
        d.drawImage(x, y/8, 2, 1, bits[y%8]*2)
        if (y%8 == 7): d.drawImage(x,y/8+1,2,1,'\x80\x80')


if __name__ == '__main__':
    
    #d = GU3900Par(dev=0)
    d = GU3900Ser(device='/dev/ttyS0', speed=38400)
    #d = GU3900USB(dev=0)
    
    d.power = 1
    d.clear()

    #d._write_screen_mode(chr(1))
    #
    #d.cancelWindow(1)
    #d.defineWindow(1, 0, 4, 256, 4)
    #
    #d.selectWindow(0)
    #d.fillRect(0,0,31,31)
    #
    #d.selectWindow(1)
    #while True:
    #    for i in xrange(256):
    #        foo = chr(random.randint(0,255)) 
    #        d.writeRamImage(i*4, '%s%s%s%s' % (foo,foo,foo,foo) )
    #        d.moveCursor(0,0)
    #        d.copyRamImage(i*4, 4, 256-i, 4)
    #        d.moveCursor(256-i,0)
    #        d.copyRamImage(0, 4, 256, 4)
    #        time.sleep(0.005)
    
        
    d.write(d.LF + '         1         2         3         4  ')
    d.write('123456789012345678901234567890123456789012')
    d.drawRect(0,0,255,63)
    d.writeMode = 1
    for y in xrange(0,63):
        for foo in xrange(0,4):
            d.drawPoint(random.randint(0,255), y)

    time.sleep(1)    
    pong(d, mode=1, n=500)

    d.clear()
    #d._write_screen_mode('\x00')
    d.writeMode = 0
    d._char_code_type(chr(1))
    d.write(''.join([ chr(c) for c in range(0x80,0xff) ]))
    d._char_code_type(chr(0))
    d.write(''.join([ chr(c) for c in range(0x20,0xff) ]))

    time.sleep(2)

    d.power = 0


