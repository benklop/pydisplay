"""
Raw raster scan driver for controllerless LCDs

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

VSYNC_LO = 0x0
VSYNC_HI = 0x20
HSYNC_LO = 0x0
HSYNC_HI = 0x40

CLOCK_LO = 0        # only used if external clock is not used
CLOCK_HI = 0x80

DATA0 = 0x01
DATA1 = 0x02
DATA2 = 0x04
DATA3 = 0x08

#
# this abstract base class presents the public interface to the LCD driver
#

class FourBitLcd:
    
    #
    # send a monochrome bitmap, stored in an 8-bit string, to the display
    #
    
    def write(self, data, address=0):

        # convert the 8-bit input into the display's 4-bit format
       
        out = []
        
        for byte in data:
            b = ord(byte)
            hi = (b>>4) & 0x0F
            out.append(hi)
            lo = b & 0x0F
            out.append(lo)

        # write the update frame out to the display
        self.buildFrame(out)
        self.sendFrame()

    def hsync(self):
        
        #self.frame.append(HSYNC_LO)
        self.frame.append(HSYNC_HI)
        self.frame.append(HSYNC_LO)
    
    def vsync(self):
        
        #self.frame.append(VSYNC_HI | HSYNC_LO)
        self.frame.append(VSYNC_HI | HSYNC_HI)
        self.frame.append(VSYNC_HI | HSYNC_LO)
            
    #
    # the core raster scan algorithm
    #
        
    def buildFrame(self, data):
        
        self.frame = []
        
        W = self.W / 4
        
        # send the first row
        self.data(data[0:W])
        
        # emit a hsync pulse to latch the row
        self.vsync()
        
        # for each scan line in the update region
        for row in xrange(1, self.H):

            offset = row * W
            
            # send the row data in
            self.data(data[offset:offset+W])
            
            # emit a hsync pulse to latch the row
            self.hsync()
        
        
#
# this concrete class implements the raster scan algorithm over an
# FTDI FT232R USB client adapter
#

import time
import threading
import Queue

try:
    
    import ftdi
    
    class FourBitLcdUsb(FourBitLcd):
        
        def __init__(self, W=320, H=240, dev=0):
            
            self.W = W
            self.H = H
            
            self.frame = []
            
            device = ftdi.getFtdiDevices()
            self.usb = ftdi.FT232R(device[dev])
            self.usb.enableBitBang()
            self.usb.setBaudRate(3)
            
            self.frameQueue = Queue.Queue()
            self.t = threading.Thread(target=self._run, args=[])
            self.t.setDaemon(True)
            self.t.start()
            
            self.write('\x00' * (H*W/8))
    
        def data(self, data):
            
            for byte in data:
                self.frame.append(CLOCK_HI|byte)
                self.frame.append(CLOCK_LO|byte)
            
        def _run(self):
            
            while True:
                
                t = time.time()
                
                try: frame = self.frameQueue.get(False)
                except: pass
                    
                try: self.usb.write(frame)
                except: pass
                
                time.sleep(0.000010)
                
                #print 1.0 / (time.time() - t)                
                

        
except: pass

try:
    
    import os
    import fcntl
    
    class FourBitLcdPar(FourBitLcd):
        
        def __init__(self, W=320, H=240, dev=0):
                
            self.fd = os.open('/dev/parport%d' % dev, os.O_RDWR)
            fcntl.ioctl(self.fd, 0x708F) # mark parport as exclusive
            fcntl.ioctl(self.fd, 0x708B) # claim the parport
            
            self.W = W
            self.H = H
            self.frame = []
            
            self.frameQueue = Queue.Queue()
            self.t = threading.Thread(target=self._run, args=[])
            self.t.setDaemon(True)
            self.t.start()
            
            self.write('\x00' * (H*W/8))
            
        def data(self, data=[0]):
            
            self.frame.extend(data)
                
        def sendFrame(self):
                
            self.frameQueue.put(self.frame[:])
                
        def send(self, data):
    
            fmt = '%c'*len(data)
            s = fmt % tuple(data)
            os.write(self.fd, s)
            
        def _run(self):
            
            while True:
                
                t = time.time()
                
                try: frame = self.frameQueue.get(False)
                except: pass
                    
                try: self.send(frame)
                except: pass
                
                time.sleep(0.000010)
                
                #print 1.0 / (time.time() - t)
            
except: pass


if __name__ == '__main__':

    import Image        
    
    W = 320; H = 240;
    #W = 160; H = 80;
    
    #d = FourBitLcdUsb(W, H, dev=0)
    d = FourBitLcdPar(W, H, dev=3)

    image = Image.open('pumpkin.jpg')
    image = image.resize((W, H)).convert('1')
    image = image.convert('L').point(lambda x: 255-x, mode='1')
    image = image.tostring()

    frame = [ image ]
    
    f = '\x00'*(W/8)
    f = f * H
    frame.append(f)
    
    f = '\xFF'*(W/8)
    f = f * H
    frame.append(f)
    
    f = '\xAA'*(W/8)
    f = f * H
    frame.append(f)
    
    f = '\xff'*(W/8) + '\x00'*(W/8)
    f = f * (H/2)
    frame.append(f)
    
    f = '\x55'*(W/8) + '\xAA'*(W/8)
    f = f * (H/2)
    frame.append(f)

    for i in [0,1,2,3,4,5] * 10:
      
        t = time.time()
        
        d.write(frame[i])
        
        #time.sleep(0.5)
        print 1.0 / (time.time() - t) 
            
        
    
