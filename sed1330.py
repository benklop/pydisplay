"""
User mode device driver for display modules using
the Seiko/Epson SED1330 family of display controllers.

tested with:
* SED1335F  10MHz 320x240
* S1D13305F 10MHz 240x128
* SED1330F   4MHz 256x128

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time

SYSTEM_SET = 0x40
SLEEP_IN   = 0x53
DISP_ON    = 0x59        
DISP_OFF   = 0x58
SCROLL     = 0x44
CSRFORM    = 0x5D
CGRAM_ADR  = 0x5C
CSRDIR     = 0x4C
HDOT_SCR   = 0x5A
OVLAY      = 0x5B
CSRW       = 0x46
CSRR       = 0x47 
MWRITE     = 0x42 
MREAD      = 0x43

SYSTEM_SET_M0_0 = 0
SYSTEM_SET_M0_1 = 0x01
SYSTEM_SET_M1_0 = 0
SYSTEM_SET_M1_1 = 0x02
SYSTEM_SET_M2_0 = 0
SYSTEM_SET_M2_1 = 0x04
SYSTEM_SET_WS_0 = 0
SYSTEM_SET_WS_1 = 0x08
SYSTEM_SET_IV_0 = 0
SYSTEM_SET_IV_1 = 0x20

SYSTEM_SET_WF_0 = 0
SYSTEM_SET_WF_1 = 0x80

OVLAY_2LAYER   = 0
OVLAY_3LAYER   = 0x10
OVLAY_TEXT     = 0
OVLAY_GRAPHICS = 0x0C
OVLAY_OR       = 0
OVLAY_XOR      = 1
OVLAY_AND      = 2
OVLAY_POR      = 3
    
class SED1330(object):
   
    def init(self):

        self.pagesize = 0x2580
        self.sl1 = self.pagesize
        self.sl2 = self.pagesize * 2
        
        cr = self.W / 8
        tcr = cr + 35

        # set the display configuration parameters for this size and speed        
        #self.systemSet(FX=7, FY=7, CR=cr-1, TCR=tcr, LF=self.H-1, AP=cr)
        self.systemSet(FX=7, FY=7, CR=cr-1, TCR=tcr, LF=self.H-1, AP=cr,
                       IV=SYSTEM_SET_IV_1, M1=SYSTEM_SET_M1_1)

        # clear the first page
        self.setCursorAddress(0)
        self.writeDisplayMemory('\x00' * self.pagesize)
                
        # clear the second page
        self.writeDisplayMemory('\x00' * self.pagesize)
        
        self.scroll(0, self.H, self.sl1, self.H, self.sl2, 0)
        self.setCursorDirection(0)
        self.setCursorType(0x07, 0x00 + 0x07)
        self.setHScrollPosition(0)
        self.setOverlayFormat(OVLAY_2LAYER | OVLAY_GRAPHICS | OVLAY_OR)
        self.setCursorAddress(0)
        self.dispOn(0x14)

    def systemSet(self, CR, TCR, LF, AP, FX=7, FY=7, M0=0, M1=0, M2=0, WS=0, IV=0, WF=0):
        """
        Initialize device and display
        """
        self.sendCommand(SYSTEM_SET)
        p1 = IV|0x10|WS|M2|M1|M0
        p2 = WF|FX
        self.sendData( '%c'*8 % (p1, p2, FY, CR, TCR, LF, AP%256, AP/256) )
        #self.sendData( '%c'*8 % (0x32, 0x07, 0x07, 0x13, 0x36, 0x4F, 0x14, 0x00) )
    
    def sleepIn(self):
        """
        Enter standby mode
        """
        self.sendCommand(SLEEP_IN)
    
    def dispOn(self, flags=0):
        """
        Enable and disable display and display flashing
        """
        self.sendCommand(DISP_ON)
        self.sendData(chr(flags))
    
    def dispOff(self):
        """
        Enable and disable display and display flashing
        """
        self.sendCommand(DISP_OFF)
    
    def scroll(self, sad1, sl1, sad2, sl2, sad3=0, sad4=0):
        """
        Set display start address and display regions
        """
        self.sendCommand(SCROLL)
        self.sendData('%c%c%c' % (sad1%256, sad1/256, sl1) )
        self.sendData('%c%c%c' % (sad2%256, sad2/256, sl2) )
        self.sendData('%c%c%c%c' % (sad3%256, sad3/256, sad4%256, sad4/256) )
        
    
    def setCursorType(self, arg0, arg1):
        """
        Set cursor type
        """
        self.sendCommand(CSRFORM)
        self.sendData('%c%c' % (arg0, arg1) )
    
    def setCGAddress(self):
        """
        Set start address of character generator RAM
        """
        self.sendCommand(CGRAM_ADR)

    def setCursorDirection(self, dir = 0):
        """
        Set direction of cursor movement
        """
        assert dir in [0,1,2,3]
        self.sendCommand(CSRDIR + dir)

    def setHScrollPosition(self, pos):
        """
        Set horizontal scroll position
        """
        self.sendCommand(HDOT_SCR)
        self.sendData(chr(pos))

    def setOverlayFormat(self, format):
        """
        Set display overlay format
        """
        self.sendCommand(OVLAY)
        self.sendData( chr(format) )

    def setCursorAddress(self, address):
        """
        Set cursor address
        """
        self.sendCommand(CSRW)
        self.sendData( '%c%c' % (address%256, address/256) )

    def getCursorAddress(self):
        """
        Read cursor address
        """
        self.sendCommand(CSRR)

    def writeDisplayMemory(self, data):
        """
        Write to display memory
        """
        self.sendCommand(MWRITE)
        self.sendData(data)
    
    def readDisplayMemory(self):
        """
        Read from display memory
        """
        self.sendCommand(MREAD)
        

try:

    import parallel # http://pyserial.sourceforge.net/pyparallel

    class SED1330Par(SED1330):
        
        def __init__(self, W, H, OSC=10000000, dev=0):
            
            p = parallel.Parallel(dev)
            self.p = p
            
            self.W = W
            self.H = H
            self.OSC = OSC
            
            # don't like this wiring?  change it!
            self.setWR   = p.setDataStrobe  # pin 1
            self.setRD   = p.setAutoFeed    # pin 14
            self.setCS   = p.setInitOut     # pin 16
            self.setA0   = p.setSelect      # pin 17
            
            self.setData = p.setData        # pins 2-9
            
            # enable the fast write if using the default wiring and the C library is installed
            try:
                assert self.setWR == p.setDataStrobe
                from ctypes import cdll
                from sys import prefix
                self._pydisplay = cdll.LoadLibrary(prefix + '/lib/python/site-packages/_pydisplay.so')
                self.sendData    = self.fastWrite
                self.sendCommand = self.fastCommand
                self.fd = p._fd
                print 'sed1330: using fast I/O library'
            except:
                self.sendData    = self.slowWrite
                self.sendCommand = self.slowCommand
                print 'sed1330: fast I/O library not available, using pyparallel'
    
            self.setRD(1)
            self.setWR(1)
            
            self.init()
            
        def slowCommand(self, cmd):
    
            self.setCS(0)
            self.setA0(1)
            self.setData(cmd)
            self.setWR(0)
            self.setWR(1)
            
        def fastCommand(self, cmd):
    
            self._pydisplay.sed1330_command(self.fd, cmd)
        
        def slowWrite(self, data):
    
            self.setCS(0)
            self.setA0(0)
            for b in data:
                self.setData(ord(b))
                self.setWR(0)
                self.setWR(1)
                
        def fastWrite(self, data):
    
            self._pydisplay.sed1330_write(self.fd, data, len(data))

except: print 'SED1330 parallel not available'

try:
    
    import ubw

    class SED1330UBW(SED1330):
        
        def __init__(self, W, H, OSC=10000000, dev=0):
            
            self.W = W
            self.H = H
            self.OSC = OSC
    
            self.ubw = ubw.MakeUsbBitWhacker(dev)
            
            # configure the direction of I/O pins 0==out 1==in
            flags = 0
            data  = 0
            self.ubw.configure(flags, data, 0)
            
            print self.ubw.version()
            
            self.W = W
            self.H = H
   
            self.init()
    
        def sendCommand(self, cmd):
            
            ubw = self.ubw
            
            try:
                
                ubw.bulkWrite(3, [cmd])
                
            except:
                
                try:
                    
                    ubw.output(3, cmd, 0)
                    ubw.output(2, cmd, 0)
                    
                except:
                    
                    ubw.reset()
                    ubw.configure(0,0,0)
                    time.sleep(1)
                    
                    ubw.output(3, cmd, 0)
                    ubw.output(2, cmd, 0)
                    
        def sendData(self, data):
            
            ubw = self.ubw
            
            data = [ord(b) for b in data]
            
            try:
                
                ubw.bulkWrite(1, data)
                
            except:
                
                try:
                    
                    for byte in data:
                        ubw.output(1, byte, 0)
                        ubw.output(0, byte, 0)
                        
                except:
                    
                    ubw.reset()
                    ubw.configure(0,0,0)
                    time.sleep(1)
                    
                    for byte in data:
                        ubw.output(1, byte, 0)
                        ubw.output(0, byte, 0)            
            
except: print 'SED1330 USB Bit Whacker not available'

if __name__ == '__main__':

    W = 160; H = 80
    #d = SED1330Par(W, H, dev=1)
    d = SED1330UBW(W, H, dev=0)

    #d.setOverlayFormat(OVLAY_2LAYER | OVLAY_TEXT | OVLAY_OR)
    #d.setCursorAddress(14*40 + 15)
    #d.writeDisplayMemory('PYDISPLAY')
    #
    #d.setCursorAddress(0x2580)
    #d.writeDisplayMemory('\xff')
    #for base in xrange(0, H*W/8, W/8):
    #    d.scroll(base,H,0x2580,H)
    #    time.sleep(0.0050)
    
    d.setOverlayFormat(OVLAY_2LAYER | OVLAY_GRAPHICS | OVLAY_OR)
    d.setCursorAddress(0)
    for i in xrange(H / 2):
        d.writeDisplayMemory('\x55'*(W/8))
        d.writeDisplayMemory('\xaa'*(W/8))
        
    d.setCursorAddress(0x0000)
    d.writeDisplayMemory('\xFF' * (W*H*2/16))
    d.setCursorAddress(0x1000)
    d.writeDisplayMemory('\xFF' * (W*H*1/16))
    d.writeDisplayMemory('\x00' * (W*H*1/16))
    for i in xrange(500):
        d.scroll(0x1000,H,0x2000,H)
        time.sleep(0.001)
        d.scroll(0x0000,H,0x2000,H)
        time.sleep(0.001)
    d.setCursorAddress(0x1000)
    d.writeDisplayMemory('\x00' * (W*H*2/16))

    time.sleep(1)
    d.setOverlayFormat(OVLAY_2LAYER | OVLAY_TEXT | OVLAY_OR)
    d.setCursorAddress(0)
    d.writeDisplayMemory(''.join([ chr(c) for c in range(0x20,0x80)]) * 8)
    d.writeDisplayMemory(''.join([ chr(c) for c in range(0xa0,0xe0)]) * 8)
    
    time.sleep(2)
    d.dispOff()
