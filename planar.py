"""
Raw raster scan driver for controllerless
Planar EL320.240 electroluminescent display

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time

VSYNC_LO = 0x0
VSYNC_HI = 0x20
HSYNC_LO = 0x0
HSYNC_HI = 0x40

CLOCK_LO = 0
CLOCK_HI = 0x80

DATA0 = 0x01
DATA1 = 0x02
DATA2 = 0x04
DATA3 = 0x08


#____ abstract base class ______________________________________________________

class EL320_240(object):
    
    def __init__(self):

        self.W = 320
        self.H = 240

    #
    # send a monochrome bitmap, stored in an 8-bit string, to the display
    #
    
    def write(self, data, address=0):

        # convert the 8-bit input into the display's 4-bit format
        out = []
        
        for byte in data:
            b = ord(byte)
            hi = (b>>4) & 0x0F
            out.append(VSYNC_HI | hi)
            lo = b & 0x0F
            out.append(VSYNC_HI | lo)

        # write the update frame out to the display
        self.buildFrame(out, address/(self.W/8))
        self.send(self.frame)
        self.send(self.frame)

    #
    # the core raster scan algorithm
    #
    
    def hsync(self):
        
        self.frame.append(VSYNC_HI | HSYNC_HI)
        self.frame.append(VSYNC_HI | HSYNC_LO)

    def vsync(self):
        
        self.frame.append(VSYNC_LO | HSYNC_LO)
        self.frame.append(VSYNC_LO | HSYNC_HI)
        self.frame.append(VSYNC_LO | HSYNC_LO)

    def data(self, data=[0]):
        
        for byte in data:
            self.frame.append(CLOCK_HI|byte)
            self.frame.append(CLOCK_LO|byte)
                
    def buildFrame(self, data, start=0):
        
        W = self.W/4
        self.frame = []
        
        stop = start + len(data)/W

        if start == 0:
         
            # clock the first scanline in
            self.data(data[0:W])
            start = 1
        
        # emit a vsync pulse to latch the first row
        self.vsync()
        
        # for each scan line in the upper margin
        for row in xrange(1, start):
            
            # emit a hsync pulse, but skip the row
            self.hsync()
            
        # for each scan line in the update region
        for row in xrange(start, stop):

            offset = (row-start) * W
            
            # clock the row data in
            self.data(data[offset:offset+W])

            # emit a hsync pulse to latch in the row
            self.hsync()
            
        for row in xrange(stop, self.H):
            
            self.hsync()


class EL640_200SK(object):
    
    def __init__(self):

        self.W = 640
        self.H = 200

    def write(self, data, address=0):

        # convert the 8-bit input into the display's 4-bit format
        out = []
        
        for byte in data:
            b = ord(byte)
            hi = (b>>4) & 0x0F
            out.append(VSYNC_LO | hi)
            lo = b & 0x0F
            out.append(VSYNC_LO | lo)

        # write the update frame out to the display
        self.buildFrame(out, address/(self.W/8))
        self.send(self.frame)
        self.send(self.frame)
           
    def data(self, data=[0]):
        
        for byte in data:
            self.frame.append(CLOCK_HI|byte)
            self.frame.append(CLOCK_LO|byte)
            
    def hsync(self):
        
        self.frame.append(VSYNC_LO | HSYNC_HI)
        self.frame.append(VSYNC_LO | HSYNC_LO)

    def vsync(self):
        
        self.frame.append(VSYNC_HI | HSYNC_LO)
        self.frame.append(VSYNC_HI | HSYNC_HI)
        self.frame.append(VSYNC_HI | HSYNC_LO)

    def buildFrame(self, data, start=0):
        
        W = self.W/4
        self.frame = []
        
        stop = start + len(data)/W

        if start == 0:
         
            # clock the first scanline in
            self.data(data[0:W])
            start = 1
        
        # emit a vsync pulse to latch the first row
        self.vsync()
        
        # for each scan line in the upper margin
        for row in xrange(1, start):
            
            # emit a hsync pulse, but skip the row
            self.hsync()
            
        # for each scan line in the update region
        for row in xrange(start, stop):

            offset = (row-start) * W
            
            # clock the row data in
            self.data(data[offset:offset+W])

            # emit a hsync pulse to latch in the row
            self.hsync()
            
        for row in xrange(stop, self.H+1):
            
            self.hsync()
            
#____ USB ______________________________________________________________________

try:

    import ftdi
    
    class EL320_240_USB(EL320_240):
        
        def __init__(self, dev=0):
            
            super(EL320_240USB, self).__init__()
            
            device = ftdi.getFtdiDevices()
            self.usb = ftdi.FT232R(device[dev])
            self.usb.enableBitBang()
              
        def send(self):
            
            try: self.usb.write(self.frame)
            except: pass
    
except:  print 'EL320_240 FTDI USB not available'

#____ parallel _________________________________________________________________


try:
    
    import os
    import fcntl
    import struct
    
    class EL320_240_Par(EL320_240):
        
        def __init__(self, dev=0):
            
            super(EL320_240_Par, self).__init__()            
            
            self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
            fcntl.ioctl(self.fd, 0x0000708F) # mark parport as exclusive
            fcntl.ioctl(self.fd, 0x0000708B) # claim the parport
            #fcntl.ioctl(self.fd, 0x40047090, struct.pack('i',0)) # set data dir to out
            #fcntl.ioctl(self.fd, 0x40047080, struct.pack('i',1<<8)) # set mode to 'compat'
            
        def data(self, data=[0]):
            
            self.frame.extend(data)
                
        def send(self, data):
    
            fmt = '%c'*len(data)
            s = fmt % tuple(data)
            os.write(self.fd, s)
            
    class EL640_200SK_Par(EL640_200SK):

        def __init__(self, dev=0):
            
            super(EL640_200SK_Par, self).__init__()            
            
            self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
            fcntl.ioctl(self.fd, 0x0000708F) # mark parport as exclusive
            fcntl.ioctl(self.fd, 0x0000708B) # claim the parport
            
        def data(self, data=[0]):
            self.frame.extend(data)
                
        def send(self, data):
    
            fmt = '%c'*len(data)
            s = fmt % tuple(data)
            os.write(self.fd, s)        

except: print 'Planar parallel not available'

if __name__ == '__main__':
    
    #d = EL320_240_USB()    
    #d = EL320_240_Par(dev=2)
    #
    #length = d.W/8
    #
    #while True:
    #
    #    d.write('\x11'*length, 2400)
    #    d.write('\x22'*length, 2400)
    #    d.write('\x44'*length, 2400)
    #    d.write('\x88'*length, 2400)
        
    d = EL640_200SK_Par(dev=2)

    length = d.W / 8 * 20

    while True:

        d.write('\x11'*length, length)
        d.write('\x22'*length, length)
        d.write('\x44'*length, length)
        d.write('\x88'*length, length)
        