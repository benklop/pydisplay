"""        
User mode device driver for Noritake GU300-series Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""


DISPLAY_MODE_GRAPHIC   = 1
DISPLAY_MODE_CHARACTER = 0

ENABLE_SCREEN_1 = 1
ENABLE_SCREEN_2 = 2

class GU300(object):
    
    def init(self):
        
        self.setWR(0)

        self.setBrightness(100)
        self.setDisplayStartAddress(screen1=0x0000, screen2=0x1000)
        self.setCursorAddress(0)
        self.writeData('\x00' * 0x2000)
        self.setCursorAddress(0)
        
        self.reset()
        
    def reset(self):

        self.enableScreen(ENABLE_SCREEN_1 | ENABLE_SCREEN_2)
        self.selectDisplayMode(DISPLAY_MODE_GRAPHIC)

    def enableScreen(self, mode):
        
        self.sendCommand(mode)
        
    def setDisplayStartAddress(self, screen1=0, screen2=0):
        
        self.sendCommand(0xA)
        self.sendData(chr(screen1%256))
        self.sendCommand(0xB)
        self.sendData(chr(screen1/256))
        self.sendCommand(0xC)
        self.sendData(chr(screen2%256))
        self.sendCommand(0xD)
        self.sendData(chr(screen2/256))
        
    def selectDisplayMode(self, mode):
        
        self.sendCommand(0x6 + mode)
        
    def writeData(self, data):
        
        self.sendCommand(0x8)
        self.sendData(data)
        self.setCS(1)
        
    def setCursorAddress(self, address):

        self.sendCommand(0xE)
        self.sendData(chr(address%256))
        self.sendCommand(0xF)
        self.sendData(chr((address/256) & 0x1F))
        
    def setBrightness(self, level):
        
        if   level <= 62.5: self.sendCommand(0x1b)
        elif level <= 75.0: self.sendCommand(0x1a)
        elif level <= 87.5: self.sendCommand(0x19)
        else: self.sendCommand(0x18)

try:
    
    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class GU300Parallel(GU300):
        
        def __init__(self, W=256, H=64, dev=0, fastwrite=True):
            
            p = parallel.Parallel(dev)
            
            self.setWR = p.setDataStrobe    # pin 1
            self.setCD = p.setAutoFeed      # pin 14
            
            self.setRD   = p.setInitOut     # pin 16
            self.setCS   = p.setSelect      # pin 17
            
            self.setRD(1)
            
            self.setData = p.setData        # pins 2-9
            
            self.W = W
            self.H = H
    
            # enable the fast write if using the default wiring and the C library is installed
            self.sendData = self.slowData
            if fastwrite:
                try:
                    assert self.setWR == p.setDataStrobe
                    assert self.setCD == p.setAutoFeed 
                    from ctypes import cdll
                    from sys import prefix
                    self._pydisplay = cdll.LoadLibrary(prefix + '/lib/python/site-packages/_pydisplay.so')
                    self.fd = p._fd
                    self.sendData = self.fastData
                    print 'gu300: using fast I/O library'
                except:
                    self.sendData = self.slowData
                    print 'gu300: fast I/O library not available, using pyparallel'
                
            self.init()
        
        def sendCommand(self, cmd):
            
            self.setCS(0)
            self.setCD(1)
            self.setData(cmd)
            self.setWR(0)
            self.setWR(1)
        
        def slowData(self, data):
    
            self.setCS(0)
            self.setCD(0)
           
            for d in data:
                
                self.setData(ord(d))
                self.setWR(0)
                self.setWR(1)
                
        def fastData(self, data):
            
            self._pydisplay.gu300_write(self.fd, data, len(data))      
    
except: print 'GU300 parallel not available'

        
if __name__ == '__main__':
    
    import time
    
    d = GU300Parallel(dev=2, fastwrite=True)
    
    d.setBrightness(100)
    
    pattern = ( ('\x55'*8) + ('\xaa'*8) ) * 128
    #pattern = '\xff' * 2048
    d.writeData(pattern)
    time.sleep(2)
    
    d.setCursorAddress(0)
    pattern = '\xff'*8 + ( '\x80' + '\x00'*6 + '\x01' ) * 254 + '\xff'*8
    d.writeData(pattern)
    time.sleep(2)
    
    d.writeData('\x00'*0x2000)
    
    