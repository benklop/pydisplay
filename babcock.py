"""
User mode device driver for Babcock DC plasma displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

def bits(byte):
    
    result = ''
    
    for i in xrange(8):
        bit = byte & 1
        result += '\x1d\x1f'[bit]
        byte >>= 1
        
    return result[::-1]
        
    
_bits = [ bits(byte) for byte in xrange(256) ]

#____ abstract base class ______________________________________________________

class GD120C280(object):
    
    def setCursorMode(self, mode):
        
        opcode = chr(0x13 + mode)
        self.write(opcode)
        
    def setCursorPosition(self, col, row):
        
        self.col = col
        self.row = row
        opcode = '\x1A%c%c%c' % ( row, col/256, col%256 )
        self.write(opcode)
        
    def setAutoCursor(self, col, row):
        
        opcode = '\x1C%c' % (row<<4|col)
        self.write(opcode)
        
    def selectOffscreenPage(self, page):
        
        opcode = '\x17%c' % page
        self.write(opcode)

    def selectDisplayPage(self, page):
        
        opcode = '\x18%c' % page
        self.write(opcode)
        self.page = page
    
    def setPixel(on=True):
        
        if on: self.write('\x1F')
        else : self.write('\x1D')
    
    def writePixels(self, data):
        
        self.setAutoCursor(0,1)

        data = [ _bits[ord(byte)] for byte in data ]
        data = ''.join(data)
                
        while len(data) > 0:
            
            self.write(data[:120])
            data = data[120:]
            
            self.col += 1
            cursor = '\x1A\x00%c%c' % (self.col/256, self.col%256)
            self.write(cursor)
        
    def init(self):
        
        self.W = 280
        self.H = 120

        #self.clear()
        self.col  = 0
        self.row  = 0
        for page in [0,1]:
            self.selectOffscreenPage(page)
            self.selectDisplayPage(page)
            self.setCursorMode(1)

#____ parallel _________________________________________________________________

try:
    
    # /WR   = /strobe pin 1
    # BUSY  = busy    pin 11
    # /A0   = GND 
    # /US    = GND
    #
    # D0-7  = pins 2-9
    
    #import os
    #import fcntl    
    #class GD120C280Par(GD120C280):
    #    
    #    def __init__(self, dev=0):
    #        
    #        self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
    #        fcntl.ioctl(self.fd, 0x708F) # mark parport as exclusive
    #        fcntl.ioctl(self.fd, 0x708B) # claim the parport
    #        
    #        self.init()
    #    
    #    def write(self, data):
    #        
    #        os.write(self.fd, data)
    
    import parallel
    import time
    
    class GD120C280Par(GD120C280):
        
        def __init__(self, dev=0):
            
            self.W = 280
            self.H = 120
            
            p = parallel.Parallel(dev)
            p.setAutoFeed(0)
            p.setInitOut(0)
            p.setSelect(0)
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.getBUSY = p.getInBusy      # pin 11
            
            self.setData = p.setData        # pins 2-9
                
            self.init()
        
        def write(self, data):
            
            oldbyte = 0
            self.setData(0)
    
            for byte in data:
                
                if oldbyte != byte:
                    
                    self.setData(ord(byte))
                    oldbyte = byte
                    
                while self.getBUSY():
                    time.sleep(0)
                
                self.setWR(0)
                self.setWR(1)
            
except: print 'Babcock GD120C280 parallel not available'

#____ USB ______________________________________________________________________

try:

    class GD120C280USB(GD120C280):
        
        def __init__(self, dev=0):
            
            assert False
            
            self.init()
            
        def write(self, data):
    
            pass
        
except: print 'Babcock GD120C280 USB not available'


if __name__ == '__main__':

    import time
    
    d = GD120C280Par(dev=0)
    
    d.write('hello, world!')
    time.sleep(2)
    
    t = time.time()
    pixels = '\xff' * (15*280)
    d.writePixels(pixels)
    print time.time() - t
    
    time.sleep(2)

    

    
    
    