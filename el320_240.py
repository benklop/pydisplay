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

inv=0; inv=1
if inv:
    VSYNC_LO = 0x20
    VSYNC_HI = 0x0
    HSYNC_LO = 0x40
    HSYNC_HI = 0x0


CLOCK_LO = 0
CLOCK_HI = 0x80

DATA0 = 0x01
DATA1 = 0x02
DATA2 = 0x04
DATA3 = 0x08

H = 240
W = 320 / 4

#
# this abstract base class presents the public interface to the
# Planar EL320.240 display driver
#

class EL320_240:
    
    def __init__(self): pass

    #
    # send a monochrome bitmap, stored in an 8-bit string, to the display
    #
    
    def write(self, data, address=0):

        # convert the 8-bit input into the display's 4-bit format
        
        out = []
        
        t = time.time()
        for byte in data:
            b = ord(byte)
            hi = (b>>4) & 0x0F
            out.append(hi)
            lo = b & 0x0F
            out.append(lo)
        #print 1.0 / (time.time() - t),

        # write the update frame out to the display
        
        #t = time.time()
        self.scan(out, address/40)
        #print 1.0 / (time.time() - t)

    #
    # the core raster scan algorithm
    #
    
    def scan(self, data, start=0):
        
        stop = start + len(data)/80;

        if start == 0:
            self.col0[0] = [data[0]]
            self.col1[0] = [data[1]]
            first  = data[1:80]
            self.col0[1] = [data[80]]
            self.col1[1] = [data[81]]
            second = data[81:160]
        else:
            first  = self.col1[0]
            second = self.col1[1]
            
        # emit a hsync pulse
        self.send(VSYNC_LO | HSYNC_HI, self.col0[0])
        
        # clock the first scanline in
        self.send(VSYNC_LO | HSYNC_LO, first)
        
        # emit a hsync pulse
        self.send(VSYNC_LO | HSYNC_HI, self.col0[1])
        
        # clock the second scanline in with vsync pulse
        self.send(VSYNC_HI | HSYNC_LO, second)

        # for each scan line in the upper margin
        for row in xrange(2, start):
            
            # emit a hsync pulse, but skip the row
            self.send(VSYNC_LO | HSYNC_HI, self.col0[row])
            self.send(VSYNC_LO | HSYNC_LO, self.col1[row])
            
        # for each scan line in the update region
        for row in xrange(start, stop):

            offset = (row-start) * 80
            
            # emit a hsync pulse
            self.send(VSYNC_LO | HSYNC_HI, data[offset:offset+1])
            
            # clock the row data in
            self.send(VSYNC_LO | HSYNC_LO, data[offset+1:offset+80])
            
            self.col0[row] = [data[offset]]
            self.col1[row] = [data[offset+1]]

        # for each remaining scan line
        for row in xrange(stop, H-1):
            
            # emit a hsync pulse, but skip the row
            self.send(VSYNC_LO | HSYNC_HI, self.col0[row])
            self.send(VSYNC_LO | HSYNC_LO, self.col1[row])
            
        # emit a hsync pulse, but skip the row
        self.send(VSYNC_LO | HSYNC_HI)
        self.send(VSYNC_LO | HSYNC_LO, [0]*79)

        self.sync()
        
        
#
# this concrete class implements the raster scan algorithm over an
# FTDI FT232R USB client adapter
#

import threading
import sched

class UsbScanDriver:
    
    def __init__(self):
        
        device = ftdi.getFtdiDevices()
        self.usb = ftdi.FT232R(device[0])        
        
        self.s = sched.scheduler(time.time, time.sleep)
        self.s.enter(0, 0, self._scan, [])
        
        self.t = threading.Thread(target=self._run, args=[])
        self.t.start()
    
    def _run(self):
        
        try: self.s.run()
        except: pass
        
    def queueNewFrame(self, frame):
        
        f = frame[:] # copy by client thread eliminates the need for locking
        self.s.enter(0, 0, self._updateFrame, [f])

    def _updateFrame(self, frame):
        
        self._frame = frame
        
        
    def _scan(self):
        
        try:
            #self.packet.append(VSYNC_HI) # leave the display on after the last frame
            self.usb.writeData(self._frame)
        except: pass
        
        self.s.enter(0.001, 0, self._scan, [])


import ftdi

class EL320_240USB(EL320_240):
    
    def __init__(self):
        
        self.W = 320
        self.H = 240
        
        device = ftdi.getFtdiDevices()
        self.usb = ftdi.FT232R(device[0])
        self.usb.enableBitBang()
        self.packet = []
        
        self.col0 = [[0]]*self.H
        self.col1 = [[0]]*self.H
        
        #self.s = UsbScanDriver()

    def send(self, sync, data=[0]):
        if sync: data = [ sync|byte for byte in data ]
        self.packet.extend(data)
        #for byte in data:
        #    self.packet.append(sync|CLOCK_HI|byte)
        #    self.packet.append(sync|CLOCK_LO|byte)
            
    def sync(self):
        try: self.usb.write(self.packet*3)
        except: pass
        #try: self.usb.write(self.packet*2)
        #except: pass
        self.packet = []
        time.sleep(0)

        
#
# this concrete class implements the display driver over a PC parallel interface
#
# probably too slow to be useful
#

import parallel # http://pyserial.sourceforge.net/pyparallel

class EL320_240Par(EL320_240):
    pass

        

if __name__ == '__main__':
    
    d = EL320_240USB()    
    
    while True:
    
        d.write('\x11'*4800, 2400)
        d.write('\x22'*4800, 2400)
        d.write('\x44'*4800, 2400)
        d.write('\x88'*4800, 2400)
        