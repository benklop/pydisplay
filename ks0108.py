"""
User mode device driver for display modules using
the Samsung KS0108 display controller.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

class KS0108(object):
    
    def init(self):
       
        self.setE(0)
        
        self.setPage(0)
        self.setAddress(0)
        self.setDisplayStartLine(0)
        self.enable()
    
    def enable(self, on=1):
        """
        Controls the display on or off. Internal status and display RAM data is
        not affected. L:OFF, H:ON
        """
        self.sendCommand(0x3E, on & 0x01)
                
    def setAddress(self, address):
        """
        Sets the Y address in the Y address counter.
        """
        self.sendCommand(0x40, address & 0x3F)
        
    def setPage(self, address):
        """
        Sets the X address at the X address register.
        """
        self.sendCommand(0xB8, address & 0x07)
        
    def setDisplayStartLine(self, address):
        """
        Indicates the display data RAM displayed at the top of the screen.
        """
        self.sendCommand(0xC0, address & 0x3F)
    
    #def readStatus(self):
    
    #def readDisplayData(self):

try:
    
    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class KS0108Par(KS0108):
        
        def __init__(self, W=128, H=64, dev=0):
            
            p = parallel.Parallel(dev)
            
            # don't like this wiring?  change it!
            self.setCS1  = p.setDataStrobe  # pin 1
            self.setCS2  = p.setAutoFeed    # pin 14
            self.setE    = p.setInitOut     # pin 16
            self.setRS   = p.setSelect      # pin 17
    
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            self.H = H
    
            self.init()   
            
        def sendCommand(self, cmd, data=0):
            self.setRS(0)   # this is a display command
            self.setE(1)    # and here it is...
            self.setData(cmd | data)
            self.setE(0)    # complete the operation
            
        def writeDisplayData(self, data):
            """
            Writes data (DB0:7) into display data RAM. After writing instruction,
            Y address is increased by 1 automatically.
            """
            self.setRS(1)  # this is display data
            for byte in data:
                self.setE(1)    # and here it is...
                self.setData(byte) 
                self.setE(0)    # complete the operation

except: print 'KS0108 parallel not available'
    
try:
    
    import ubw
    import time
    
    class KS0108UBW(KS0108):
        
        def __init__(self, W=128, H=64, dev=0):
            
            self.ubw = ubw.MakeUsbBitWhacker(dev)
            
            # configure the direction of I/O pins 0==out 1==in
            flags = 0
            data  = 0
            self.ubw.configure(flags, data, 0)
            
            print self.ubw.version()
            
            self.W = W
            self.H = H
            
            self.CS = 0xC
            #self.ubw.bulkConfigure(2|self.CS, 0,0,1,1)
    
            self.init()
        
        def setE(self, on):
            self.ubw.output(on|self.CS, 0, 0)
            
        def setCS1(self, on):
            if on: self.CS |= 0x4
            else:  self.CS &= 0xB
            
        def setCS2(self, on):
            if on: self.CS |= 0x8
            else:  self.CS &= 0x7
            
        def sendCommand(self, cmd, arg):
            
            ubw = self.ubw
            
            try:
                
                ubw.bulkWrite(self.CS, [cmd|arg])
                
            except:
                
                try:
                    
                    ubw.output(1|self.CS, cmd|arg, 0)
                    ubw.output(0|self.CS, cmd|arg, 0)
                    
                except:
                    
                    ubw.reset()
                    ubw.configure(0,0,0)
                    time.sleep(1)
                    
                    ubw.output(1|self.CS, cmd|arg, 0)
                    ubw.output(0|self.CS, cmd|arg, 0)
                    
        
        def writeDisplayData(self, data):
            
            ubw = self.ubw
            
            try:
                
                ubw.bulkWrite(2|self.CS, data)
                    
            except:
                
                try:
                    
                    for byte in data:
                        ubw.output(3|self.CS, byte, 0)
                        ubw.output(2|self.CS, byte, 0)
                        
                except:
                    
                    ubw.reset()
                    ubw.configure(0,0,0)
                    time.sleep(1)
                    
                    for byte in data:
                        ubw.output(3|self.CS, byte, 0)
                        ubw.output(2|self.CS, byte, 0)
                        
except: print 'KS0108 USB Bit Whacker not available'

font5x7 = {
    ' ' : [ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ],
    '!' : [ 0x00, 0x00, 0x00, 0x4F, 0x00, 0x00 ],
    '"' : [ 0x00, 0x00, 0x07, 0x00, 0x07, 0x00 ],
    '#' : [ 0x00, 0x14, 0x7F, 0x14, 0x7F, 0x14 ],
    '$' : [ 0x00, 0x24, 0x2A, 0x7F, 0x2A, 0x12 ],
    '%' : [ 0x00, 0x23, 0x13, 0x08, 0x64, 0x62 ],
    '&' : [ 0x00, 0x36, 0x49, 0x55, 0x22, 0x50 ],
    '\'' : [ 0x00, 0x00, 0x05, 0x03, 0x00, 0x00 ],
    '(' : [ 0x00, 0x00, 0x1C, 0x22, 0x41, 0x00 ],
    ')' : [ 0x00, 0x00, 0x41, 0x22, 0x1C, 0x00 ],
    '*' : [ 0x00, 0x14, 0x08, 0x3E, 0x08, 0x14 ],
    '+' : [ 0x00, 0x08, 0x08, 0x3E, 0x08, 0x08 ],
    ',' : [ 0x00, 0x00, 0x50, 0x30, 0x00, 0x00 ],
    '-' : [ 0x00, 0x08, 0x08, 0x08, 0x08, 0x08 ],
    '.' : [ 0x00, 0x00, 0x60, 0x60, 0x00, 0x00 ],
    '/' : [ 0x00, 0x20, 0x10, 0x08, 0x04, 0x02 ],
    '0' : [ 0x00, 0x3E, 0x51, 0x49, 0x45, 0x3E ],
    '1' : [ 0x00, 0x00, 0x42, 0x7F, 0x40, 0x00 ],
    '2' : [ 0x00, 0x42, 0x61, 0x51, 0x49, 0x46 ],
    '3' : [ 0x00, 0x21, 0x41, 0x45, 0x4B, 0x31 ],
    '4' : [ 0x00, 0x18, 0x14, 0x12, 0x7F, 0x10 ],
    '5' : [ 0x00, 0x27, 0x45, 0x45, 0x45, 0x39 ],
    '6' : [ 0x00, 0x3C, 0x4A, 0x49, 0x49, 0x30 ],
    '7' : [ 0x00, 0x01, 0x71, 0x09, 0x05, 0x03 ],
    '8' : [ 0x00, 0x36, 0x49, 0x49, 0x49, 0x36 ],
    '9' : [ 0x00, 0x06, 0x49, 0x49, 0x29, 0x1E ],
    ':' : [ 0x00, 0x00, 0x36, 0x36, 0x00, 0x00 ],
    ';' : [ 0x00, 0x00, 0x56, 0x36, 0x00, 0x00 ],
    '<' : [ 0x00, 0x08, 0x14, 0x22, 0x41, 0x00 ],
    '=' : [ 0x00, 0x14, 0x14, 0x14, 0x14, 0x14 ],
    '>' : [ 0x00, 0x41, 0x22, 0x14, 0x08, 0x00 ],
    '?' : [ 0x00, 0x02, 0x01, 0x51, 0x09, 0x06 ],
    '@' : [ 0x00, 0x32, 0x49, 0x79, 0x41, 0x3E ],
    'A' : [ 0x00, 0x7E, 0x11, 0x11, 0x11, 0x7E ],
    'B' : [ 0x00, 0x7F, 0x49, 0x49, 0x49, 0x36 ],
    'C' : [ 0x00, 0x3E, 0x41, 0x41, 0x41, 0x22 ],
    'D' : [ 0x00, 0x7F, 0x41, 0x41, 0x22, 0x1C ],
    'E' : [ 0x00, 0x7F, 0x49, 0x49, 0x49, 0x41 ],
    'F' : [ 0x00, 0x7F, 0x09, 0x09, 0x09, 0x01 ],
    'G' : [ 0x00, 0x3E, 0x41, 0x49, 0x49, 0x7A ],
    'H' : [ 0x00, 0x7F, 0x08, 0x08, 0x08, 0x7F ],
    'I' : [ 0x00, 0x00, 0x41, 0x7F, 0x41, 0x00 ],
    'J' : [ 0x00, 0x20, 0x40, 0x41, 0x3F, 0x01 ],
    'K' : [ 0x00, 0x7F, 0x08, 0x14, 0x22, 0x41 ],
    'L' : [ 0x00, 0x7F, 0x40, 0x40, 0x40, 0x40 ],
    'M' : [ 0x00, 0x7F, 0x02, 0x0C, 0x02, 0x7F ],
    'N' : [ 0x00, 0x7F, 0x04, 0x08, 0x10, 0x7F ],
    'O' : [ 0x00, 0x3E, 0x41, 0x41, 0x41, 0x3E ],
    'P' : [ 0x00, 0x7F, 0x09, 0x09, 0x09, 0x06 ],
    'Q' : [ 0x00, 0x3E, 0x41, 0x51, 0x21, 0x5E ],
    'R' : [ 0x00, 0x7F, 0x09, 0x19, 0x29, 0x46 ],
    'S' : [ 0x00, 0x46, 0x49, 0x49, 0x49, 0x31 ],
    'T' : [ 0x00, 0x01, 0x01, 0x7F, 0x01, 0x01 ],
    'U' : [ 0x00, 0x3F, 0x40, 0x40, 0x40, 0x3F ],
    'V' : [ 0x00, 0x1F, 0x20, 0x40, 0x20, 0x1F ],
    'W' : [ 0x00, 0x3F, 0x40, 0x38, 0x40, 0x3F ],
    'X' : [ 0x00, 0x63, 0x14, 0x08, 0x14, 0x63 ],
    'Y' : [ 0x00, 0x07, 0x08, 0x70, 0x08, 0x07 ],
    'Z' : [ 0x00, 0x61, 0x51, 0x49, 0x45, 0x43 ],
    '[' : [ 0x00, 0x00, 0x7F, 0x41, 0x41, 0x00 ],
    ']' : [ 0x00, 0x00, 0x41, 0x41, 0x7F, 0x00 ],
    '^' : [ 0x00, 0x04, 0x02, 0x01, 0x02, 0x04 ],
    '_' : [ 0x00, 0x40, 0x40, 0x40, 0x40, 0x40 ],
    '`' : [ 0x00, 0x00, 0x01, 0x02, 0x04, 0x00 ],
    'a' : [ 0x00, 0x20, 0x54, 0x54, 0x54, 0x78 ],
    'b' : [ 0x00, 0x7F, 0x48, 0x48, 0x48, 0x30 ],
    'c' : [ 0x00, 0x38, 0x44, 0x44, 0x44, 0x00 ],
    'd' : [ 0x00, 0x30, 0x48, 0x48, 0x48, 0x7F ],
    'e' : [ 0x00, 0x38, 0x54, 0x54, 0x54, 0x18 ],
    'f' : [ 0x00, 0x08, 0x7E, 0x09, 0x09, 0x02 ],
    'g' : [ 0x00, 0x0C, 0x52, 0x52, 0x52, 0x3E ],
    'h' : [ 0x00, 0x7F, 0x08, 0x04, 0x04, 0x78 ],
    'i' : [ 0x00, 0x00, 0x44, 0x7D, 0x40, 0x00 ],
    'j' : [ 0x00, 0x20, 0x40, 0x44, 0x3D, 0x00 ],
    'k' : [ 0x00, 0x00, 0x7F, 0x10, 0x28, 0x44 ],
    'l' : [ 0x00, 0x00, 0x41, 0x7F, 0x40, 0x00 ],
    'm' : [ 0x00, 0x7C, 0x04, 0x18, 0x04, 0x78 ],
    'n' : [ 0x00, 0x7C, 0x04, 0x04, 0x04, 0x78 ],
    'o' : [ 0x00, 0x38, 0x44, 0x44, 0x44, 0x38 ],
    'p' : [ 0x00, 0x7C, 0x14, 0x14, 0x14, 0x08 ],
    'q' : [ 0x00, 0x08, 0x14, 0x14, 0x14, 0x7C ],
    'r' : [ 0x00, 0x7C, 0x08, 0x04, 0x04, 0x08 ],
    's' : [ 0x00, 0x48, 0x54, 0x54, 0x54, 0x20 ],
    't' : [ 0x00, 0x04, 0x3F, 0x44, 0x44, 0x20 ],
    'u' : [ 0x00, 0x3C, 0x40, 0x40, 0x20, 0x7C ],
    'v' : [ 0x00, 0x1C, 0x20, 0x40, 0x20, 0x1C ],
    'w' : [ 0x00, 0x3C, 0x40, 0x20, 0x40, 0x3C ],
    'x' : [ 0x00, 0x44, 0x28, 0x10, 0x28, 0x44 ],
    'y' : [ 0x00, 0x0C, 0x50, 0x50, 0x50, 0x3C ],
    'z' : [ 0x00, 0x44, 0x64, 0x54, 0x4C, 0x44 ],
    '{' : [ 0x00, 0x00, 0x08, 0x36, 0x41, 0x00 ],
    '|' : [ 0x00, 0x00, 0x00, 0x7F, 0x00, 0x00 ],
    '}' : [ 0x00, 0x00, 0x41, 0x36, 0x08, 0x00 ],
    '\xB0' : [ 0x00, 0x00, 0x07, 0x05, 0x07, 0x00 ]
}

class KS0108Module(KS0108UBW):
    """
    By itself, the KS0108 controller doesn't do much.
    
    A usable module might add some text and graphics drawing functions.
    This doesn't get used in the library interface, but it illustrates
    the use of the device.
    """
    
    def __init__(self, dev=0):
        KS0108UBW.__init__(self, dev=dev)
        self.clear()
        
    def writeChar(self, c):
        for b in font5x7[c]:
            self.setCS1(self._col < 64)
            self.setCS2(self._col > 63)
            if self._col == 64: self.setAddress(0)
            self._col += 1
            self.writeDisplayData([b])
            
        if self._col > 125:
            self.moveCursor(0, (self._row + 1) % 8)
        
    def write(self, str):
        for c in str:
            self.writeChar(c)
    
    def moveCursor(self, col=0, row=0):
        self._col = col
        self._row = row
        
        self.setCS1(1)
        self.setCS2(1)
        self.setPage(row)
        
        if col < 64:
            self.setCS2(0)
            self.setAddress(col)
        else:
            self.setCS1(0)
            self.setAddress(col - 64)
        
    def clear(self, pattern=0):
        self.setCS1(1)
        self.setCS2(1)
        for row in xrange(8):
            self.setPage(row)
            for col in xrange(64):
                self.writeDisplayData([pattern])
        self.moveCursor(0,0)

    
def truchet(d):
    import random

    pattern = (0x08,0x04,0x02,0x01,0x80,0x40,0x20,0x10)
    #pattern = (0x08,0x08,0x04,0x03,0xc0,0x20,0x10,0x10)
    tiles = ( pattern, pattern[::-1] )
    
    # build a table of screen addresses
    addr = [ (x,y) for x in xrange(0,128,8) for y in xrange(8) ]
    
    row = 0
    
    while 1:
        t = time.time()
        
        # for each (randomized) address location
        random.shuffle(addr)
        for a in addr:
            # draw a random tile 
            tile = random.choice(tiles)
            d.moveCursor(a[0], a[1])
            d.writeDisplayData(tile)
            #time.sleep(0.005)
        d.setCS1(1)
        d.setCS2(1)
        d.setDisplayStartLine(row)
        row += 1
        row %= 64
        
        #print time.time() - t
            
            
if __name__ == '__main__':
    
    import time

    d = KS0108Module(dev=0)
    
    d.clear(0xff)
    time.sleep(1)
    d.clear()
    
    font = font5x7.keys()
    font.sort()
    f = [c for c in font*4]
    d.write(f)
       
    time.sleep(2)
    
    d.clear()
    d.write('1234567890123456789012')
    d.write(' hello, KS0108!')
    
    d.setCS1(1); d.setCS2(1)
    for row in xrange(48):
        d.setDisplayStartLine(row)
        time.sleep(0.001)
        
    time.sleep(2)
  
    truchet(d)

    d.clear()
    d.enable(0)
    