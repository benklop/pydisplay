"""
User mode device driver for Noritake GU7000-series Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

BS  = '\x08'
HT  = '\x09'
LF  = '\x0A'
HOM = '\x0B'
CR  = '\x0D'
CLR = '\x0C'

#____ abstract base class ______________________________________________________

class GU7000(object):
    
    def __init__(self, W, H):

        self.W = W
        self.H = H
        
    def showCursor(self, show=1):

        self.write('\x1f\x43%c' % show)
        
    def setCursor(self, x, y):

        self.write('\x1F\x24%c%c%c%c' % (x%256, x/256, y%256, y/256))
        
    def clearDisplay(self):

        self.write(CLR)
        
    def initDisplay(self):

        self.write('\x1B\x40')
        
    def setWriteMixMode(self, mode):

        self.write('\x1f\x77%c' % mode)
        
    def setBrightness(self, brightness):

        brightness = brightness * 8 / 100
        self.write('\x1f\x58%c' % brightness)
        
    def displayBitImage(self, w, h, image):

        args = ( w%256, w/256, h%256, h/256, image)
        self.write('\x1f\x28\x66\x11%c%c%c%c\x01%s' % args)
        
    def reverseDisplay(self, reverse=True):

        self.write('\x1f\x72%c' % reverse)
        
#____ serial ___________________________________________________________________

try:
    
    import serial # http://pyserial.sourceforge.net
    
    class GU7000Ser(GU7000):
        
        def __init__(self, W, H, dev='/dev/ttyS0'):
            
            GU7000.__init__(self, W, H)
            self._ser = serial.Serial(dev, baudrate=38400, writeTimeout=1)
            self._ser.open()
            
        def write(self, data):
            
            self._ser.write(data)
        
except: print 'GU7000 serial not available'
        
#____ parallel _________________________________________________________________

# VFD  | PARPORT
# /WR  | /strobe pin 1
# BUSY | busy pin 11
# D0-7 | D0-7 pins 2-9

try:
    
    import os
    import fcntl
    
    class GU7000Par(GU7000):
        
        def __init__(self, W, H, dev=0):
            
            GU7000.__init__(self, W, H)
            
            self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
            fcntl.ioctl(self.fd, 0x708F) # mark parport as exclusive
            fcntl.ioctl(self.fd, 0x708B) # claim the parport
            
        def write(self, data):
            
            os.write(self.fd, data)
    
except: print 'GU7000 parallel not available'

#____ USB ______________________________________________________________________

try:
    
    import ftdi
    import sys

    # these are tuning parameters
    USB_CHUNK_SIZE = 64
    BAUD_RATE = 0x2800
    
    class GU7000USB(GU7000):
    
        def __init__(self, W, H, dev=0):
            
            GU7000.__init__(self, W, H)
            
            device = ftdi.getFtdiDevices()
            self.usb = ftdi.FT232R(device[dev])
            self.usb.setBaudRate(BAUD_RATE)
            self.usb.enableBitBang()
            
        def write(self, data):
    
            while len(data) > 0:
                
                try: self.usb.write(data[:USB_CHUNK_SIZE])
                except: pass
                
                data = data[USB_CHUNK_SIZE:]
                
except: print 'GU7000 FTDI USB not available'
    
if __name__ == '__main__':
    
    import time
    
    #d = GU7000Par(140, 16, dev=0)
    #d = GU7000USB(140, 16, dev=0)
    d = GU7000Ser(140, 16, dev='/dev/ttyS0')
    
    d.clearDisplay()

    d.write('hello, noritake dude')
    
    d.setCursor(0,1)    
    image = ''.join( [ chr(i) for i in xrange(140) ] )
    d.displayBitImage(140, 1, image)
    
    time.sleep(2)
    d.clearDisplay()

    