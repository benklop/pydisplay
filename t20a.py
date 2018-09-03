"""
User mode device driver for Noritake T20A Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time

BS  = '\x08'
TAB = '\x09'
LF  = '\x0A'
FF  = '\x0C'
CR  = '\x0D'
CLR = '\x0E'
ESC = '\x1B'

class T20A(object):

    def init(self):
        
        self.write(ESC + 'I')
        time.sleep(0.1) # unit needs a moment to process
            
    def clear(self):
        
        self.write(CLR + FF)
        
    def setCursorMode(self, mode):
        
        assert mode in [0,1,2,3]
        self.write(chr(0x14+mode))
        
    def setCharacterTable(self, table):
        
        assert table in [0,1]
        self.write(chr(0x18+table))
        
    def setLineEndingMode(self, mode):
        
        assert mode in [0,1]
        self.write(chr(0x11+mode))
        
    def defineCharacter(self, chr, data):
        
        self.write(ESC + 'C' + chr + data)
    
    def moveCursor(self, x, y):
        
        self.write(ESC + 'H' + chr(y*self.W + x))
    
    def setBrightness(self, b):
        
        assert 0 <= b <= 100
        self.write(ESC + 'L' + chr(b*255/100))
        
    def selectFlickerlessMode(self):
        
        self.write(ESC + 'S')
    
try:
    
    import parallel
    
    class T20APar(T20A):
        
        def __init__(self, W=40, dev=0):

            p = parallel.Parallel(dev)
            
            self.setWR   = p.setDataStrobe  # pin 1
            self.getBusy = p.getInBusy      # pin 11
            self.setCS   = p.setAutoFeed    # pin 14
        
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            
            self.init()
            
        def write(self, data):
            
            #self.setCS(0)
            
            for byte in data:
                self.setData(ord(byte)) # setting the data bits in advance gives BUSY time to clear
                while self.getBusy(): pass
                self.setWR(0)        # toggle display /WR pin to signal a write
                self.setWR(1)
                
            #self.setCS(1)                
        
except: print 'T20A parallel not available'

try:
    
    import serial # http://pyserial.sourceforge.net
    
    class T20ASerial(T20A):
        
        def __init__(self, W=40, device='/dev/ttyS0', speed=19200):
            
            self._ser = serial.Serial(device, speed, parity=serial.PARITY_EVEN, writeTimeout=1)
            self._ser.open()
            
            self.W = W
            
            self.init()
            
        def write(self, s):
            
            self._ser.write(s)        

except: print 'T20A serial not available'

if __name__ == '__main__':
    
    #d = T20ASerial(device='/dev/ttyS0')
    #d = T20ASerial(device='/dev/ttyUSB0')
    d = T20APar(dev=2)
    d.setCursorMode(2)
    d.setCharacterTable(0)
    d.setLineEndingMode(1)
    d.setBrightness(100)
    d.moveCursor(11, 1)
    #d.defineCharacter('!', '\x0f\x0f\x0f\x0f\x07')
    d.write('hello, noritake!')
    time.sleep(1)
    d.setLineEndingMode(1)
    for c in range(0x20,0xff):
        d.write(chr(c))
        #time.sleep(0.1)
    time.sleep(2)
    d.clear()
