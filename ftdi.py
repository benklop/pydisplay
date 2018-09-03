"""
User mode interface to FTDI FT232R/FT245R usb device controllers.

Only the 'bit-bang' mode is required to control a device like an LCD.
That is what we care about, so we will only implement enough to enable
the bit-wise read and write functions.

On Linux systems, the ftdi_sio driver must first be unloaded in order for
the direct driver to work.  The command to do this is usually 'rmmod' or
'modprobe -r'.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import usb # http://pyusb.berlios.de/

def getFtdiDevices():
    result = []
    for bus in usb.busses():
        devices = bus.devices
        for dev in devices:
            if dev.idVendor == 0x0403 :#and dev.idProduct == 0xFFFF:
                result.append(dev)
    return result
                
class FT232R(object):
    
    def __init__(self, device):
            
        self.device = device.open()
        try:
            s = self.device.getString(2,30)
            print 'opened device:', s
        except: pass

        self.setBaudRate(0)        
        
    def enableBitBang(self, enable=1, direction=0xff):
        value = (enable << 8) | direction
        self.device.controlMsg(requestType=0x40, request=0x0B, value=value, buffer=0) 

    def setBaudRate(self, rate):
        #self.device.controlMsg(requestType=0x40, request=0x03, value=0x000f, buffer=0)
        self.device.controlMsg(requestType=0x40, request=0x03, value=rate, buffer=0)
    
    def writeCbus(self, mask, data):
        value = 0x2000 | mask | data
        self.device.controlMsg(requestType=0x40, request=0x0B, value=value, buffer=0)
    
    def writeByte(self, byte):
        self.device.controlMsg(requestType=0x40, request=0x0B, value=0x0400 | ~byte, buffer=0)
        #self.device.controlMsg(requestType=0x40, request=0x0B, value=0x0000, buffer=0)
            
    def write(self, data):

        result = self.device.bulkWrite(0x2, data)


if __name__ == '__main__':
    
    device = getFtdiDevices()
    
    d = FT232R(device[0])
    d.enableBitBang(1)
    #d.setBaudRate(0x2800)
    #d.setBaudRate(4800)

    data = [0xff,0,0xff,0] * 256
    
    while True:
        try:
            d.write(data)
        except:
            pass


    