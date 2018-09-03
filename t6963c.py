"""
User mode device driver for display modules using
the Toshiba T6963C display controller.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

MODE_CG_ROM               = 0x80
MODE_OR                   = 0x80
MODE_AND                  = 0x83

DISPLAY_MODE_OFF          = 0x90
DISPLAY_MODE_CURSOR       = 0x92
DISPLAY_MODE_CURSOR_BLINK = 0x93
DISPLAY_MODE_TEXT         = 0x94
DISPLAY_MODE_GRAPHICS     = 0x98

try:
    
    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class T6963C(object):
    
        def __init__(self, W=128, H=64, dev=0):
            
            p = parallel.Parallel(dev)
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.setRD   = p.setAutoFeed    # pin 14
            self.setCE   = p.setInitOut     # pin 16
            self.setCD   = p.setSelect      # pin 17
    
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            self.H = H
    
            self.init()
            
        def init(self):
            
            self.setRD(1)
            self.setWR(1)
    
            self.setGraphicsHomeAddress(0)
            self.setGraphicsArea(self.W/8)
        
            self.setMode(MODE_CG_ROM | MODE_OR)
            self.setDisplayMode(DISPLAY_MODE_GRAPHICS)
            
            self.setAddressPointer(0)
            self.autoWrite('\x00' * (self.W/8 * self.H))
            
            self.setAddressPointer(0)
    
        
        def sendCommand(self, cmd):
            self.setCD(1)
            self.setCE(0)
            self.setWR(0)
            self.setData(cmd)
            self.setWR(1)
            self.setCE(1)
        
        def sendData(self, data):
            self.setCD(0)
            for c in data:
                self.setCE(0)
                self.setWR(0)
                self.setData(ord(c))
                self.setWR(1)
                self.setCE(1)
        
        def startAutoWrite(self):
            self.sendCommand(0xB0)
            
        def autoReset(self):
            self.sendCommand(0xB2)
            
        def autoWrite(self, data):
            self.startAutoWrite()
            self.sendData(data)
            self.autoReset()
       
        def setCursorPointer(self, x, y):
            self.sendData('%c%c' % (x, y))
            self.sendCommand(0x21)
            
        def setOffsetPointer(self, offset):
            self.sendData(chr(offset))
            self.sendCommand(0x22)
            
        def setAddressPointer(self, address):
            self.sendData('%c%c' % (address%256, address/256))
            self.sendCommand(0x24)
    
        def setTextHomeAddress(self, address):
            self.sendData('%c%c' % (address%256, address/256))
            self.sendCommand(0x40)
        
        def setTextArea(self, col):
            self.sendData('%c%c' % (col,0) )
            self.sendCommand(0x41)
            
        def setGraphicsHomeAddress(self, address):
            self.sendData('%c%c' % (address%256, address/256))
            self.sendCommand(0x42)
            
        def setGraphicsArea(self, col):
            self.sendData('%c%c' % (col,0) )
            self.sendCommand(0x43)
            
        def setMode(self, mode):
            self.sendCommand(mode)
            
        def selectCursorPattern(self, pattern):
            self.sendCommand(0xA0 + pattern)
            
        def setDisplayMode(self, mode):
            self.sendCommand(mode)
            
        def writeData(self, data, autoincrement=1):
            assert autoincrement in [-1,0,1]
            assert 0
            
        def setBit(self, bit, reset=False):
            assert 0
        
except: pass

if __name__ == '__main__':
    
    d = T6963C(128, 64, dev=0)
    
    d.setTextHomeAddress(0)
    d.setTextArea(d.W/8)
    d.setAddressPointer(0)
    d.setCursorPointer(0, 0)
    
    d.setDisplayMode(DISPLAY_MODE_TEXT | DISPLAY_MODE_CURSOR_BLINK)
    d.autoWrite('\x48\x45\x4c\x4c\x4f\x0c\x5f\x54\x16\x19\x16\x13\x43\x5f\x5f\x5f' * 8) # 'hello, t6963c   '
        