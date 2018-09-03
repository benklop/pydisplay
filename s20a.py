"""
User mode device driver for Noritake S20A Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time
    
BS  = '\x08'
TAB = '\x09'
LF  = '\x0A'
#FF  = '\x0C'
CR  = '\x0D'
#CLR = '\x0E'
ESC = '\x1B'


try:

    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class S20A(object):
        
        def __init__(self, W=40, dev=0):
            
            p = parallel.Parallel(dev)
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.setA0   = p.setAutoFeed    # pin 14
            self.setRD   = p.setInitOut     # pin 16
            self.setCS   = p.setSelect      # pin 17
            
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            
            self.RD = 1
            
            self.init()
            
        def write(self, s):
            
            self.setCS(0)
            self.setA0(0)
            
            for c in s:
                self.setData(ord(c)) 
                self.setWR(0)        # toggle display /WR pin to signal a write
                self.setWR(1)
                self.setWR(1)        # a couple of bonus calls to pad the timing (pretty hackish)
                self.setWR(1)
                self.setWR(1)
               
            self.setCS(1)
    
        def init(self):
            
            self.setCS(0)
            self.setA0(1)
            self.setData(0x50)
            self.setWR(0)
            self.setWR(1)
            self.setCS(1)
            
            time.sleep(0.1) # unit needs a moment to process
                
        def clear(self):
            self.write(CR + ' ' * 80)
            
        def setCursorMode(self, mode):
            assert mode in [0,1,2,3]
            self.write(chr(0x13+mode))
            
        #def setCharacterTable(self, table):
        #    assert table in [0,1]
        #    self.write(chr(0x18+table))
            
        def setLineEndingMode(self, mode):
            assert mode in [0,1]
            self.write(chr(0x11+mode))
            
        #def defineCharacter(self, chr, data):
        #    self.write(ESC + 'C' + chr + data)
        
        def moveCursor(self, x, y):
            
            self.setCS(0)
            self.setA0(1)
            self.setData(y*self.W + x)
            self.setWR(0)
            self.setWR(1)
            #self.setCS(1)
        
        #def setBrightness(self, b):
        #    assert 0 <= b <= 100
        #    self.write(ESC + 'L' + chr(b*255/100))
            
        #def selectFlickerlessMode(self):
        #    self.write(ESC + 'S')
    
except: pass

if __name__ == '__main__':

    d = S20A(dev=0)
    d.setCursorMode(2)
    #d.setCharacterTable(0)
    d.setLineEndingMode(1)
    #d.setBrightness(100)
    d.moveCursor(11, 1)
    #d.defineCharacter('!', '\x0f\x0f\x0f\x0f\x07')
    d.write('hello, noritake!')
    time.sleep(1)
    d.setLineEndingMode(1)
    for c in range(0x20,0xff):
        d.write(chr(c))
    time.sleep(2)
    d.clear()
