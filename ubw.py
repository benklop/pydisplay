"""
User mode device driver for USB Bit Whacker

Should work anywhere pySerial works, including Windows, MacOS, Linux, and BSD

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""
    
import serial # http://pyserial.sourceforge.net
import time

# factory method will create the appropriate object to match the
# firmware of the attached device
#
# apparently the person who wrote this is using linux

def MakeUsbBitWhacker(dev=0):
    
    dev = '/dev/ttyACM%d' % dev
    s = serial.Serial(dev, baudrate=115200, writeTimeout=10)
    s.open()
    s.flush()
    s.write('V\n')
    s.flush()
    version = s.readline().strip()
    
    if version == 'UBW FW D Version 1.1.0':
        device = UBW_D_1_1(s)
    elif version == 'UBW FW D Version 1.2.0':
        device = UBW_D_1_2(s)
    elif version == 'UBW FW D Version 1.3.0':
        device = UBW_D_1_3(s)
    else:
        # assume the best case!
        device = UBW_D_1_4(s)
        
    device.reset()
    print device.version()
    return device
    
class UBW_D_1_1:
    
    def __init__(self, serial):
        self.serial = serial

    def write(self, data):
        self.serial.write(data)
        self.serial.flush()
        
    def configure(self, dirA, dirB, dirC):
        self.write('C,%d,%d,%d,0\n' % (dirA, dirB, dirC))
    
    def output(self, portA, portB, portC=0):
        self.write('O,%d,%d,%d\n' % (portA, portB, portC))
    
    def input(self):
        self.write('I\n');
        input = self.serial.readline()
        input = input.strip().split(',')
        return tuple(input[1:])
        
    def version(self):
        self.write('V\n')
        return self.serial.readline()
    
    def reset(self):
        self.write('R\n')
        
class UBW_D_1_2(UBW_D_1_1):
    
    def configure(self, dirA, dirB, dirC, analogInputCount=0):
        self.write('C,%d,%d,%d,%d\r' % (dirA, dirB, dirC, analogInputCount))
        
    def sampleAnalogInputs(self):
        self.write('A\r')
        input = self.serial.readline()
        input = input.strip().split(',')
        return tuple(input[1:])
    
    def memoryRead(self, address):
        self.write('MR,%d\r' % address)
        input = self.serial.readline()
        input = input.strip().split(',')
        return tuple(input[1:])
    
    def memoryWrite(self, address, value):
        self.write('MW,%d,%d\r' % (address, value) )
    
    def pinDirection(self, port, pin, dir):
        self.write('PD,%d,%d,%d\r' % (port, pin, dir) )
    
    def pinInput(self, port, pin):
        self.write('PI,%d,%d\r' % (port, pin) )
        input = self.serial.readline()
        return (0,1)[input == 'PI,1']
    
    def pinOutput(self, port, pin, value):
        self.write('PO,%d,%d\r' % (port, pin, value) )
        

class UBW_D_1_3(UBW_D_1_2):
    
    def write(self, data):
        self.serial.write(data)
        result = self.serial.readline().strip()
        self.serial.flush()
        return result
        
    def configure(self, dirA, dirB, dirC, analogInputCount=0):
        result = self.write('C,%d,%d,%d,%d\n' % (dirA, dirB, dirC, analogInputCount))
        assert result == 'OK'
    
    def input(self):
        result = self.write('I\n');
        result = result.split(',')
        return tuple(result[1:])
        
    def version(self):
        result = self.write('V\n')
        return result
    
    def output(self, portA, portB, portC=0):
        result = self.write('O,%d,%d,%d\n' % (portA, portB, portC))
        assert result == 'OK'
    
    def reset(self):
        result = self.write('R\n')
        assert result == 'OK'

    def sampleAnalogInputs(self):
        result = self.write('A\n')
        result = result.split(',')
        return tuple(result[1:])
    
    def memoryRead(self, address):
        result = self.write('MR,%d\n' % address)
        result = result.split(',')
        return tuple(result[1:])
    
    def memoryWrite(self, address, value):
        result = self.write('MW,%d,%d\n' % (address, value) )
        assert result == 'OK'
    
    def pinDirection(self, port, pin, dir):
        result = self.write('PD,%d,%d,%d\n' % (port, pin, dir) )
        assert result == 'OK'
    
    def pinInput(self, port, pin):
        result = self.write('PI,%d,%d\n' % (port, pin) )
        return (0,1)[result == 'PI,1']
    
    def pinOutput(self, port, pin, value):
        result = self.write('PO,%d,%d\n' % (port, pin, value) )
        assert result == 'OK'
        
class UBW_D_1_4(UBW_D_1_3):
    
    def bulkConfigure(self, init, waitmask, waitdelay, strobemask, strobedelay):
        result = self.write('BC,%d,%d,%d,%d,%d\n' % (init, waitmask, waitdelay, strobemask, strobedelay) )
        assert result == 'OK'
        
    def bulkOutput(self, data):
        arg = 'BO,%s\n' % data
        self.serial.write(arg)
        #result = self.write(arg)
        #assert result == 'OK'
        
    def bulkWrite(self, init, data, waitmask=0, waitdelay=0, strobemask=1, strobedelay=1):
        
        arg = ''
        for byte in data:
            arg += '%02X' % byte
            
        result = self.write('BC,%d,%d,%d,%d,%d\nBO,%s\n' %
                            (init, waitmask, waitdelay, strobemask, strobedelay, arg[:48]))
        assert result == 'OK'
        arg = arg[48:]

        while len(arg) > 0:
            self.bulkOutput(arg[:56])
            arg = arg[56:]
            
        self.serial.flush()


if __name__ == '__main__':
    
    device = MakeUsbBitWhacker(dev=0)
    
    device.reset()
    print device.version()
    device.configure(0,0,0)
    device.output(0xaa,0x55,0)
    print device.input()
    device.reset()
    print device.input()
    time.sleep(1)
    
    device.reset()
    device.configure(0,0,0)
    device.bulkConfigure(2|4|8,0,0,1,1)
    
    while True:
        device.bulkOutput('000102030405060708090A0B0C0D0E0F101112131415161718191A1B1C')#1D')
        #device.bulkOutput('1E1F20212223242526272829ABCDEF
        #time.sleep(0.1)
    
