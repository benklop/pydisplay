"""
User mode device driver for display modules using
Seiko/Epson SED1520 display controllers.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

try:
    
    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class SED1520(object):
        
        def __init__(self, dev = 0):
            
            p = parallel.Parallel(dev)
            
            self.setA0 = p.setAutoFeed    # pin 14
            self.setE1 = p.setInitOut     # pin 16
            self.setE2 = p.setSelect      # pin 17
            
            self.setData = p.setData        # pins 2-9
            
            self.W = 122
            self.H = 32
            
            self.init()
            
        def init(self):
            
            for chip in [1,2]:
                
                self.selectChip(chip)
                self.setE(0)
                self.enableDisplay(0)
                self.reset()
                self.sendCommand(0xA0)  # forward column addressing
                self.sendCommand(0xA4)  # static mode off
                self.sendCommand(0xA9)  # 1/32 duty cycle
                self.enableDisplay(1)
                self.setDisplayStartLine(0)
                for page in xrange(4):
                    self.setPageAddress(page)
                    self.setColumnAddress(0)
                    self.writeDisplayData('\x00' * 61)
                self.setPageAddress(0)
                self.setColumnAddress(0)
    
        def selectChip(self, chip):
            
            self.setE = (self.setE1, self.setE2)[chip-1]
            
        def sendCommand(self, cmd):
            
            self.setA0(0)
            self.setData(cmd)
            self.setE(1)
            self.setE(0)
            
        def enableDisplay(self, enable=1):
            
            self.sendCommand(0xAE + enable)
        
        def setDisplayStartLine(self, address):
            
            self.sendCommand(0xC0 + (address & 0x1F))
            
        def setPageAddress(self, address):
            
            self.sendCommand(0xB8 + (address & 0x3))
        
        def setColumnAddress(self, address):
            
            self.sendCommand(address & 0x7F)
        
        def writeDisplayData(self, data):
            
            self.setA0(1)
            
            for d in data:
                
                self.setData(ord(d))
                self.setE(1)
                self.setE(0)
        
        def reset(self):
            
            self.sendCommand(0xE2)
            
except: pass
        
if __name__ == '__main__':
    
    d = SED1520(0)
    
    d.selectChip(1)
    d.writeDisplayData('\x55' * 61)
    d.selectChip(2)
    d.writeDisplayData('\x55' * 61)
    