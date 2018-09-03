"""
User mode device driver for Noritake GU3000-series Vacuum Fluorescent Displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import os

class GU3900DMA(object):
        
    def init(self):
        self.setWR(1)
        self.setDisplayStartAddress(0)
        self.setBrightness(100)
        
    def writeBitImage(self, image, address=0):
        length = len(image)
        data = '\x02\x44\x00\x46' # opcode
        data += '%c%c%c%c' % ( address % 256, address / 256, length % 256, length / 256 )
        data += image
        self.sendData(data)
        
    def setDisplayStartAddress(self, address):
        data  = '\x02\x44\x00\x53' # opcode
        data += '%c%c' % ( address % 256, address / 256 )
        self.sendData(data)
    
    def synchronizeDisplay(self, sync = 1):
        data  = '\x02\x44\x00\x57' # opcode
        data += chr(sync)
        self.sendData(data)
                
    def setBrightness(self, value):
        assert 0 <= value <= 100
        data  = '\x02\x44\x00\x58' # opcode
        data += chr(0x10 + value * 2 / 25)
        self.sendData(data)

try:
    
    import parallel # http://pyserial.sourceforge.net/pyparallel
    
    class GU3900DMAParallel(GU3900DMA):
        
        def __init__(self, W=256, H=64, dev=0):
            
            p = parallel.Parallel(dev)
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.getRDY  = p.getInBusy      # pin 11
            
            self.setData = p.setData        # pins 2-9
            
            self.W = W 
            self.H = H
            
            # enable the fast write if using the default wiring and the C library is installed
            try:
                assert self.setWR == p.setDataStrobe
                assert self.getRDY == p.getInBusy
                from ctypes import cdll
                from sys import prefix
                self._pydisplay = cdll.LoadLibrary(prefix + '/lib/python/site-packages/_pydisplay.so')
                self.sendData = self.fastWrite
                self.fd = p._fd
                self.synchronizeDisplay(1)
                print 'gu3900dma: using fast I/O library'
            except:
                self.sendData = self.slowWrite
                print 'gu3900dma: fast I/O library not available, using pyparallel'
                
            self.init()
            
        def slowWrite(self, data):
            for b in data:
                self.setData(ord(b))            # setting the data bits in advance gives the RDY flag time to set
                while not self.getRDY(): pass   # wait for display RDY
                self.setWR(0)                 
                self.setWR(1)                   # toggle display /WR pin to signal a write
            
        def fastWrite(self, data):
            self._pydisplay.gu3900_write(self.fd, data, len(data))
      
except: print 'GU3900DMA parallel not available'

if __name__ == '__main__':
    
    import time
    
    d = GU3900DMAParallel(W=256, H=64, dev=1)
    d.synchronizeDisplay(1)
    frame1 = 256*8
    d.writeBitImage('\x00'*frame1*2, 0)
    col = 0
    p1 = '\x55'*frame1
    p2 = '\x00'*frame1
    while 1:
        t = time.time()
        d.writeBitImage(p1, col*8)
        d.setDisplayStartAddress(0)
        d.writeBitImage(p2, frame1 + col*8)
        d.setDisplayStartAddress(frame1)
        print 2 / (time.time() - t)
        
    