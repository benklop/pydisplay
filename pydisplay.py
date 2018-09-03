"""
Graphics interface to supported display types.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import Image
from ImageDraw import ImageDraw, Draw
import ImageFont
import ImageChops

print ''

import ks0108
import t6963c
import sed1330
import sed1520
import noritake
import planar
import babcock
import lcd

import time

   
def MakeDisplay(type, *args, **kwds):
    type = type.upper()
    display = { 'T6963C'     : T6963C,
                'KS0108'     : KS0108,
                'HD61202'    : KS0108,
                'GU3900DMA'  : GU3900DMA,
                'GU3900'     : GU3900,
                'GU7000'     : GU7000,
                'GU311'      : GU311,
                'GU300'      : GU300,
                'GU355'      : GU300,
                'GU372'      : GU300,                
                'SED1330'    : SED1330,
                'SED1335'    : SED1330,
                'SED133x'    : SED1330,
                'SED1D13305' : SED1330,
                'SED1520'    : SED1520,
                'EL320_240'  : EL320_240,
                'EL640_200SK': EL640_200SK,
                'GD120C280'  : GD120C280,
                'LCD4'       : FourBitLcd }
    
    return display[type](*args, **kwds)

class PyDisplay(object):
    
    def __init__(self, display, transpose=False):
        self.W = display.W
        self.H = display.H
        self.display = display
        self.clear()
        
    def clear(self):
        self.image = Image.new('1', (self.display.W, self.display.H), color=1)
        self.refresh(Image.new('1', (self.display.W, self.display.H), color=0))
             
    def bitmap(self, xy, bitmap, fill=None):
        t = time.time();
        image = self.image.copy()
        image.paste(bitmap, xy)
        (x, y) = xy
        (w, h) = bitmap.size
        self.refresh( image, (x, y, x+w, y+h) )
        #print 'bitmap: ', 1.0 / (time.time() - t)
        
    def text(self, xy, text, fill=None, font=None, anchor=None):
        #text = text.replace(' ','_') # nasty workaround for PIL bug on amd64
        image = self.image.copy()
        Draw(image).text(xy, text, fill, font, anchor)
        self.refresh(image)
        
    _imageop = ( 'arc', 'chord', 'line', 'shape', 'pieslice', 'point', 'polygon',
                 'rectangle', 'ellipse')
    
    for op in _imageop:
        exec "def %s(self, *args, **keys): self.imageop(ImageDraw.%s, *args, **keys) " % (op, op)

    def imageop(self, op, *args, **keys):
        t = time.time();
        image = self.image.copy()
        op(Draw(image), *args, **keys)
        self.refresh(image)
        #print str(op), 1.0 / (time.time() - t)

class FourBitLcd(PyDisplay):
    
    def __init__(self, W=320, H=240, dev=0, bus='usb'):
        if bus == 'usb' :
            display = lcd.FourBitLcdUsb(W, H, dev)
        elif bus == 'par' :
            display = lcd.FourBitLcdPar(W, H, dev)
        PyDisplay.__init__(self, display)
        
    def write(self, data, address=0):
        self.display.write(data)
        
    def bitmap(self, xy, bitmap, fill=None):
        t = time.time();
        image = self.image.copy()
        image.paste(bitmap, xy)
        self.refresh(image)
        
    def refresh(self, image, bbox=None):

        # send the updated rows    
        update = image.tostring()
        self.write(update)

        # update the framebuffer
        self.image = image    

        
class RowWiseRefresh(PyDisplay):
    
    def refresh(self, image, bbox=None):

        if bbox == None:        
            # find the difference from the current framebuffer
            bbox = ImageChops.difference(image, self.image).getbbox()
            
        if bbox != None:
            
            (left, top, right, bottom) = bbox

            # send the updated rows    
            update = image.crop((0,top,self.display.W,bottom))
            update = update.tostring()
            self.write(update, top*self.display.W/8) 

            # update the framebuffer
            self.image = image
            
            
class T6963C(RowWiseRefresh):

    def __init__(self, W=320, H=240, dev=0):
        display = t6963c.T6963C(W, H, dev)
        PyDisplay.__init__(self, display)
        
    def write(self, data, address):
        self.display.setAddressPointer(address)
        self.display.autoWrite(data)


class SED1330(RowWiseRefresh):
    
    def __init__(self, W=320, H=240, OSC=10000000, dev=0, bus='par'):
        if bus == 'usb' :
            display = sed1330.SED1330UBW(W, H, OSC, dev)
        elif bus == 'par' :
            display = sed1330.SED1330Par(W, H, OSC, dev)
        PyDisplay.__init__(self, display)
        
    def clear(self):
        self.write('\x00' * 0x8000, 0)
        PyDisplay.clear(self)
        
    def write(self, data, address):
        self.display.setCursorAddress(address)
        self.display.writeDisplayMemory(data)
            

class EL320_240(RowWiseRefresh):
    
    def __init__(self, dev=0, bus='usb'):
        if bus == 'par':
            display = planar.EL320_240_Par(dev)
        elif bus == 'usb':
            display = planar.EL320_240_USB(dev)
        PyDisplay.__init__(self, display)
        
    def write(self, data, address):
        self.display.write(data, address)

class EL640_200SK(RowWiseRefresh):
    
    def __init__(self, dev=0, bus='usb'):
        if bus == 'par':
            display = planar.EL640_200SK_Par(dev)
        elif bus == 'usb':
            display = planar.EL640_200SK_USB(dev)
        PyDisplay.__init__(self, display)
        
    def write(self, data, address):
        self.display.write(data, address)

    def refresh(self, image, bbox=None):

        if bbox == None:        
            # find the difference from the current framebuffer
            bbox = ImageChops.difference(image, self.image).getbbox()
            
        if bbox != None:
            
            (left, top, right, bottom) = bbox

            # send the updated rows    
            update = image.crop((0,0,self.display.W,bottom))
            update = update.tostring()
            self.write(update, 0) 

            # update the framebuffer
            self.image = image        
        
class ColumnWiseRefresh(PyDisplay):

    def clear(self):
        
        self.write('\x00' * (self.display.W/8) * self.display.H, 0)
        PyDisplay.clear(self)
        
    def refresh(self, image, bbox=None):
        
        # find the difference from the current framebuffer
        if bbox == None:
            bbox = ImageChops.difference(image, self.image).getbbox()
            
        if bbox != None:
            
            (left, top, right, bottom) = bbox
            left /= 8; left *= 8
            right *= 8; right /= 8

            # get the pixels to be updated
            update = image.crop((left,0,right,self.display.H))
            # rotate the update into the display's vertical address orientation
            update = update.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
            # send the update
            update = update.tostring()
            self.write(update, left*(self.display.H/8))
            
            # update the framebuffer
            self.image = image
            
            
class GD120C280(ColumnWiseRefresh):

    def __init__(self, dev=0, bus='par'):
        if bus == 'par' :
            display = babcock.GD120C280Par(dev)
        elif bus == 'usb' :
            display = babcock.GD120C280USB(dev)
        PyDisplay.__init__(self, display)
        self.page = 0
        
    def bitmap(self, xy, bitmap, fill=None):
        t = time.time();
        image = self.image.copy()
        image.paste(bitmap, xy)
        (x, y) = xy
        (w, h) = bitmap.size
        self.refresh(image)
        #print 'bitmap: ', 1.0 / (time.time() - t)
        
    def write(self, data, address):
        
        display = self.display

        for page in [0,1]:
            
            display.selectOffscreenPage(page)
            display.setCursorMode(1)
            
            (col, row) = (address/15, address%15)
            display.setCursorPosition(col, row)
            display.writePixels(data)
            
            display.selectDisplayPage(page)
        
    def clear(self):
        self.write('\x00' * (280*15), 0)
        self.image = Image.new('1', (self.display.W, self.display.H), color=0)
       
    
class GU3900DMA(ColumnWiseRefresh):
    
    def __init__(self, W=256, H=64, dev=0):
        display = noritake.GU3900DMAParallel(W, H, dev)
        PyDisplay.__init__(self, display)
        
    def clear(self):
        self.write('\x00' * (self.W*self.H/4), 0)
        PyDisplay.clear(self)
        
    def bitmap(self, xy, bitmap, fill=None):
        self.setDisplayStartAddress(0)
        super(GU3900DMA, self).bitmap(xy, bitmap, fill)
        
    def write(self, data, address):
        self.display.writeBitImage(data, address)

    def setDisplayStartAddress(self, *args, **kwds):
        self.display.setDisplayStartAddress(*args, **kwds)

class GU3900(ColumnWiseRefresh):
    
    def __init__(self, W=256, H=64, dev=0, bus='par'):
        if bus == 'par' :
            display = noritake.GU3900Par(W, H, dev)
        elif bus == 'ser' :
            display = noritake.GU3900Ser(W, H, dev)
        elif bus == 'usb' :
            display = noritake.GU3900USB(W, H, dev)
        PyDisplay.__init__(self, display)

    def clear(self):
        self.display.clear()
        PyDisplay.clear(self)
        
    def write(self, data, address):
        W = len(data) / 8
        self.display.moveCursor(address/8,address%8)
        arg = '%c%c%s%s' % ( W%256, W/256, '\x08\x00\x01', data )
        self.display._display_rt_bit_image(arg)

    def setDisplayStartAddress(self, *args, **kwds):
        self.display.setDisplayStartAddress(*args, **kwds)
        
class GU7000(ColumnWiseRefresh):
    
    def __init__(self, W=140, H=16, dev=0, bus='usb'):
        if bus == 'par' :
            display = noritake.GU7000Par(W, H, dev)
        elif bus == 'ser' :
            display = noritake.GU7000Ser(W, H, dev)
        elif bus == 'usb' :
            display = noritake.GU7000USB(W, H, dev)
        PyDisplay.__init__(self, display)
        
    def write(self, data, address):
        H = self.H / 8
        W = len(data) / H
        self.display.setCursor(address/H,address%H)
        self.display.displayBitImage(W, H, data)

    def setDisplayStartAddress(self, *args, **kwds):
        pass
    
class GU300(ColumnWiseRefresh):
    
    def __init__(self, W=256, H=64, dev=0, fastwrite=True):
        self.W = W
        self.H = H
        display = noritake.GU300Parallel(W, H, dev, fastwrite)
        PyDisplay.__init__(self, display)

    def clear(self):
        self.write('\x00' * 0x2000, 0)
        PyDisplay.clear(self)
        
    def write(self, data, address):
        self.display.setCursorAddress(address)
        self.display.writeData(data)
        
    def setDisplayStartAddress(self, *args, **kwds):
        self.display.setDisplayStartAddress(*args, **kwds)

            
class GU311(PyDisplay):
    
    def __init__(self, dev=0):
        display = noritake.GU311(dev)
        display.W = 128
        display.H = 32
        PyDisplay.__init__(self, display)
    
    def clear(self):
        self.display.clear()
        PyDisplay.clear(self)
        
    def refresh(self, image, bbox=None):
        
        # find the difference from the current framebuffer
        bbox = ImageChops.difference(image, self.image).getbbox()
        if bbox != None:
            
            (left, top, right, bottom) = bbox
            right *= 8; right /= 8
            left /= 8; left *= 8
            top /= 8;
            bottom += 7; bottom /= 8;
            
            # for each Nx8 row segment
            for row in xrange(top, bottom):        
                y = row * 8
                update = ''
                # build a horizontal array of 8-bit vertical stripes
                for x in xrange(left, right, 8):
                    # get an 8x8 chunk and rotate into the display's vertical address orientation
                    chunk = image.crop((x, y, x+8, y+8)).transpose(Image.ROTATE_270)
                    # add this 8x8 chunk to the update
                    update += chunk.tostring()
                
                # write out the update for this Nx8 row
                self.display.graphicWrite(update, left*4 + row)
                    
            # update the framebuffer
            self.image = image

        
class KS0108(PyDisplay):
    
    def __init__(self, W=128, H=64, dev=0, bus='usb'):
        if bus == 'par' :
            display = ks0108.KS0108Par(W, H, dev)
        elif bus == 'usb' :
            display = ks0108.KS0108UBW(W, H, dev)
        PyDisplay.__init__(self, display)

    def write(self, data):
        self.display.writeDisplayData([ ord(c) for c in data ])

    def refresh(self, image, bbox=None):
        
        # find the difference from the current framebuffer
        if bbox == None:
            bbox = ImageChops.difference(image, self.image).getbbox()
            
        if bbox != None:
                
            (left, top, right, bottom) = bbox
            right *= 8; right /= 8
            left /= 8; left *= 8
            top /= 8;
            bottom += 7; bottom /= 8;
            
            # for each Nx8 row segment
            for page in xrange(top, bottom):
                
                # if there's something to paint on chip 1
                if left < 64:
        
                    # select chip 1
                    self.display.setCS1(1)
                    self.display.setCS2(0)
                    
                    # reset the cursor
                    self.display.setPage(page)
                    self.display.setAddress(left)
                    
                    start = left
                    stop = 64
                    if (right < 64): stop = right
                    
                    # add each 8x8 chunk to the update region
                    segment = ''
                    for x in xrange(start,stop,8):
                        y = page*8
                        # get an 8x8 chunk and rotate it into the display's vertical pixel format
                        chunk = image.crop((x, y, x+8, y+8)).transpose(Image.ROTATE_270)
                        # add this 8x8 chunk to the update
                        segment += chunk.tostring()
                        
                    # send the update for this segment
                    self.write(segment)
    
                # if there's something to paint on chip 2
                if right > 63:
                
                    # select chip 2
                    self.display.setCS1(0)
                    self.display.setCS2(1)
                    
                    start = 64
                    if (left > 64): start = left
                    stop = right
                    
                    # reset the cursor
                    self.display.setPage(page)
                    self.display.setAddress(start-64)
            
                    # add each 8x8 chunk to the update region
                    segment = ''
                    for x in xrange(start,stop,8):
                        y = page*8
                        # get an 8x8 chunk and rotate it into the display's vertical pixel format
                        chunk = image.crop((x, y, x+8, y+8)).transpose(Image.ROTATE_270)
                        # add this 8x8 chunk to the update
                        segment += chunk.tostring()
                    
                    # send the update for this segment
                    self.write(segment)
                
            # update the framebuffer
            self.image = image

class SED1520(PyDisplay):
    
    def __init__(self, dev=0):
        display = sed1520.SED1520(dev)
        PyDisplay.__init__(self, display)
        
    def refresh(self, image, bbox=None):
        
        # find the difference from the current framebuffer
        if bbox == None:
            bbox = ImageChops.difference(image, self.image).getbbox()
            
        if bbox != None:
            
            (left, top, right, bottom) = bbox
            right *= 8; right /= 8
            left /= 8; left *= 8
            top /= 8;
            bottom += 7; bottom /= 8;
            
            # for each Nx8 row segment
            for page in xrange(top, bottom):
                
                # if there's something to paint on chip 1
                if left < 64:
        
                    # select chip 1
                    self.display.selectChip(1)
                    
                    # reset the cursor
                    self.display.setPageAddress(page)
                    self.display.setColumnAddress(0)
                    
                    # add each 8x8 chunk to the update region
                    segment = ''
                    for x in xrange(0,64,8):
                        
                        y = page*8
                        # get an 8x8 chunk and rotate it into the display's vertical pixel format
                        chunk = image.crop((x, y, x+8, y+8)).transpose(Image.ROTATE_270)
                        # add this 8x8 chunk to the update
                        segment += chunk.tostring()
                        
                    # send the update for this segment
                    self.display.writeDisplayData(segment[:61][::-1])
    
                # if there's something to paint on chip 2
                if right > 60:
                
                    # select chip 2
                    self.display.selectChip(2)
                    
                    # reset the cursor
                    self.display.setPageAddress(page)
                    self.display.setColumnAddress(0)
            
                    # add each 8x8 chunk to the update region
                    segment = ''
                    for x in xrange(61,61+64,8):
                        
                        y = page*8
                        # get an 8x8 chunk and rotate it into the display's vertical pixel format
                        chunk = image.crop((x, y, x+8, y+8)).transpose(Image.ROTATE_270)
                        # add this 8x8 chunk to the update
                        segment += chunk.tostring()
                    
                    # send the update for this segment
                    self.display.writeDisplayData(segment[:61][::-1])
                
            # update the framebuffer
            self.image = image