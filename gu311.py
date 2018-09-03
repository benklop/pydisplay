"""
User mode device driver for Noritake GU128x32-311 Vacuum Fluorescent Display.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

try:
    
    import os
    import fcntl
    import time
    
    # VFD   | PARPORT
    # WR    | /strobe pin 1
    # CS    | GND
    # RESET | +5V
    # BLANK | +5V
    # BUSY  | Busy    pin 11
    
    # D0-7  | pins 2-9
    
    USE_FCNTL = False
    import sys
    if sys.platform == 'linux2':
        #USE_FCNTL = False
        USE_FCNTL = True
    
    class GU311(object):
        
        def __init__(self, dev=0):
            
            if USE_FCNTL:
                self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
                fcntl.ioctl(self.fd, 0x708F) # mark parport as exclusive
                fcntl.ioctl(self.fd, 0x708B) # claim the parport
            else:
                import parallel
                p = parallel.Parallel(dev)
                self.setWR    = p.setDataStrobe # pin 1
                self.getBUSY  = p.getInBusy     # pin 11
                self.setData  = p.setData       # pins 2-9
                self.setWR(1)
            
            self.init()
            
        def init(self):
            
            self.setBrightness(100)
            self.selectCharPage(1)
            self.selectFlickerless(1)
            self.enable()
            self.clear()
            
        def enable(self, on=True):
    
            self.sendCommand('ST'[on])
            
        def selectFlickerless(self, on=True):
    
            self.sendCommand('QR'[on])
            time.sleep(0.1)
            
        def selectCharPage(self, page):
            
            assert page in [0,1]
            self.sendCommand('01'[page])
            
        def sendData(self, data):

            if USE_FCNTL:            
                os.write(self.fd, data)
            else:
                for b in data:
                    self.setData(ord(b))
                    while self.getBUSY(): pass
                    self.setWR(0)
                    self.setWR(1)                
            
        def clear(self):
            
            self.sendCommand('P')
            
        def sendCommand(self, cmd):
            
            self.sendData('\x01\x4f%c' % cmd)
            
        def setBrightness(self, value):
            
            assert 0 <= value <= 100
            value = 100 - value
            self._brightness = value
            arg = 0x61 + (value*16/100)
            self.sendCommand(arg)
            
        def characterWrite(self, str, col=0, row=0, mode='S'):
            
            addr = row*22 + col
            message  = '\x01C%c%c%c%s' % (addr, len(str), mode, str)
            self.sendData(message)
                
        def graphicWrite(self, image, address, mode='S'):
            
            imglen = len(image)
            arg = (address/256, address%256, imglen/256, imglen%256, mode, image)
            message  = '\x01H%c%c%c%c%c%s' % arg
            self.sendData(message)
    
except: print 'GU311 parallel not available'

def pong(d, mode='O', loop=1000000):
    
    import random
    
    bits = '\x01\x02\x04\x08\x10\x20\x40\x80'
    x = 0; y = 0
    dx = dy = 1
    for i in xrange(loop):
        if x < 0-dx: dx = random.randint(1,3)
        if x > 127-dx: dx = -2
        x = (x+dx)%128
        if y < 0-dy: dy = 1
        if y > 31-dy: dy = -1
        y = (y+dy)%32
        address = x*4 + y/8
        d.graphicWrite(bits[y%8], address, mode)
        time.sleep(0.01)
        d.graphicWrite(bits[y%8], address, mode='E')
    
    
if __name__ == '__main__':

    d = GU311(dev=2)
    d.setBrightness(50)
    
    d.characterWrite('Noritake', 7, 0)
    d.characterWrite('GU128x32-311', 5, 2)
    time.sleep(2)
    pong(d, mode='O')
    d.enable(0)

    