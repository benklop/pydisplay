"""
Script to show current time, weather, and rss feeds
on a variety of graphics displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import Image
from ImageDraw import ImageDraw, Draw
import ImageFont
import ImageChops

import feedparser # http://www.feedparser.org
import time

from widget import Widget
import pydisplay

def MakeTicker(display, *args, **kwds):
    
    if isinstance(display, pydisplay.GU3900DMA):
        return GU3900DMA(display, *args, **kwds)
    
    if isinstance(display, pydisplay.GU3900):
        return GU3900(display, *args, **kwds)
    
    if isinstance(display, pydisplay.GU300):
        return GU300(display, *args, **kwds)
    
    if isinstance(display, pydisplay.SED1330):
        return SED1330(display, *args, **kwds)
    
    if isinstance(display, pydisplay.EL320_240):
        return EL320_240(display, *args, **kwds)

    assert False

class RssTicker(Widget): 

    def __init__(self, scheduler, rect, display, feeds):
        
        Widget.__init__(self, scheduler, rect)
        
        self.feeds = feeds
        
        self.tickerlength = 0
        self.tickeroffset = 0
        
        self.display = display
        self.ticker = MakeTicker(display, scheduler, rect)

        for size in xrange(200,0,-1):
            self.font = ImageFont.truetype('DejaVuSans.ttf', size)
            w,h = self.font.getsize('qgjy9')
            if h < self.H: break        
        

    # build a bitmap of a font-rendered string
    def render(self, text, font):
        
        # calculate the buffer size for the ticker text
        image = Image.new('1', (0,0))
        W,_ = Draw(image).textsize(text=text, font=font)
        H = self.H
        
        # render the ticker
        image = Image.new('1', (W,H), color=0)
        Draw(image).text((0,0), text=text, font=font, fill=0xff)
        #image.show(command='display')
        
        return image
        
        
    def renderRssFeed(self, feed):
    
        parse = feedparser.parse(feed)
        
        ticker = ''
        
        for entry in parse.entries:
            headline = entry.title
            if entry.has_key('summary'): headline += ': ' + entry.summary
            headline = headline.encode('utf-8').replace('\n', ' ')
            ticker += headline + (' '*10)
            
        return self.render(ticker, self.font)

    
    def refresh(self):

        self.ticker.draw(self.tickeroffset)
        self.tickeroffset += 1
        

    def start(self):
        
        self.update(self.feeds)
        
        
    def update(self, feeds):
        
        # if the ticker is finished scrolling, get a new one
        if self.tickeroffset >= self.tickerlength:
            
            try:
                if len(feeds) < 1: feeds = self.feeds
                ticker = self.renderRssFeed(feeds[0])
                self.ticker.setTicker(ticker)
                self.tickerlength = ticker.getbbox()[2] + self.display.W
                self.tickeroffset = 0
                self.schedule(0, 1, self.update, (feeds[1:],))
            except:
                self.schedule(0, 1, self.update, (feeds[1:],))
            
        # else the ticker is still scrolling, advance and refresh
        else:
            
            self.schedule(0.005, 1, self.update, (feeds,))
            self.refresh()
            
            
class Ticker(Widget): pass

# code for rendering the clock graphics to the display is very device-specific
#
# here is a good example for a display that has overlayed graphics planes and
# display memory offsets


class GU300(Ticker):

    def __init__(self, display, scheduler, rect):
        
        super(GU300, self).__init__(scheduler, rect)
        
        self.display = display
        self.ticker = ''
        self.framebuffer = 0x0800
       
        
    def setTicker(self, ticker):
        
        t,l,r,b = ticker.getbbox()
        image = Image.new('1', (r-l, self.display.H))
        image.paste(ticker, (0,self.Y))
        ticker = image.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
        self.ticker = ticker.tostring() + '\x00'*8*self.display.W

        
    # smoothly scroll a long bitmap through a circular frame buffer
    def draw(self, offset):
        
        # the visible window slides across a buffer twice its length,
        # when it reaches the end of the buffer, it should wrap around
        # to the beginning again
        base = 0x1000
        window = 0x800
        increment = 8
        start = offset*increment
        scanline = self.ticker[start:start+increment]
        address = base + (start % window)
        
        # write a new column past the end of the current window
        self.display.write(scanline, address + window)
        
        # advance the window by one column
        self.display.setDisplayStartAddress(screen2 = address + increment)
    
        # write the same column to the end of the circular buffer, which is
        # the last column *before* the start of the window
        self.display.write(scanline, address)

    
# code for rendering the clock graphics to the display is very device-specific
#
# here is a good example for a display that has pageable offscreen memory, but
# no graphics overlay

class GU3900DMA(Ticker):
    
    def __init__(self, display, scheduler, rect):
        
        super(GU3900DMA, self).__init__(scheduler, rect)
        
        self.display = display
        self.framebuffer = 0x0800
        self.ticker =  Image.new('1', (0,0))


    def setTicker(self, ticker):
        
        t,l,r,b = ticker.getbbox()
        W,H = r-l, self.H
        image = Image.new('1', (W+self.W*2,H), color=0)
        image.paste(ticker, (self.W,0))
        self.ticker = image

        
    def draw(self, offset):
        
        if not offset % 2:
            
            image = self.display.image.copy()
            ticker = self.ticker.crop((offset,0,offset+self.W,self.H))
            image.paste(ticker, (self.X,self.Y))
            image = image.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
            image = image.tostring()
                
            # draw the clock to the framebuffer
            self.display.write(image, self.framebuffer)
            
            # page in the framebuffer
            self.display.setDisplayStartAddress(self.framebuffer)
            self.framebuffer += 0x0800
            self.framebuffer %= 0x1000
        
        
    
# code for rendering the clock graphics to the display is very device-specific
# 
# this device has an offscreen display memory page *and* a separate RAM area
# with a bitblt function with raster ops (copy, and, or, xor)
#
# NOTE: this is not at all portable.
#       it is extremely specific to superclock on the gu256x64-3900
class GU3900(Ticker):
    
    def __init__(self, display, scheduler, rect):
        
        super(GU3900, self).__init__(scheduler, rect)
        
        self.display = display.display
        
        self.display.defineWindow(1, 0, 0, 256, 5)
        self.display.defineWindow(2, 0, 5, 256, 3)
        self.display.writeRamImage(0, '\x00'*1024)
        self.image = Image.new('1', (256, 64), color=1)
        self.ticker = ''

    def setTicker(self, image):
        
        bbox = image.getbbox()
        image = image.crop((0, 0, bbox[2], 24))
        image = image.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
        self.ticker = image.tostring() + '\x00'*3*self.W
        
        
    def draw(self, offset):
        
        increment = 3
        start = offset * increment
        scanline = self.ticker[start:start+increment]
        
        self.display.selectWindow(2)
       
        # write to the end of the circular buffer
        i = offset % 256
        self.display.writeRamImage(i*3, scanline )
        i += 1
        i %= 256
        
        # copy the tail of the buffer to the head of the display
        self.display.moveCursor(0,0)
        self.display.copyRamImage(i*3, 3, 256-i, 3)
        
        # copy the head of the buffer to the tail of the display
        self.display.moveCursor(256-i,0)
        self.display.copyRamImage(0, 3, i, 3)
        
        self.display.selectWindow(1)

# code for rendering the clock graphics to the display is very device-specific
#
# another device with overlayed graphics planes

class SED1330(Ticker):
    
    def __init__(self, display, scheduler, rect):
        
        super(SED1330, self).__init__(scheduler, rect)

        W,H = display.W, display.H
        
        self.display = display.display
        self.screen2 = 0x2580
        self.display.scroll(0, H, self.screen2, H)
        display.clear()
        self.ticker = Image.new('1', (W,H), color=0)
        
        
    def setTicker(self, ticker):
        
        t,l,r,b = ticker.getbbox()
        W,H = r-l, self.H
        image = Image.new('1', (W+self.W*2,H), color=0)
        image.paste(ticker, (self.W,0))
        self.ticker = image

        
    def draw(self, offset):

        W = self.display.W
        
        image = self.ticker
        image = image.crop((offset, 0, offset+W, self.H))
        image = image.tostring()
        
        base = self.screen2 + (self.Y)*W/8
    
        self.display.setCursorAddress(base)
        self.display.writeDisplayMemory(image)    
    

# code for rendering the clock graphics to the display is very device-specific

try:
    
    class EL320_240(Ticker):
        
        def __init__(self, display, scheduler, rect):
            
            super(EL320_240, self).__init__(scheduler, rect)
            
            self.display = display
            self.ticker = Image.new('1', (0,0), color=1)
            self.display.clear()
                
            
        def setTicker(self, ticker):
            
            t,l,r,b = ticker.getbbox()
            W,H = r-l, self.H
            image = Image.new('1', (W+self.W*2,H), color=0)
            image.paste(ticker, (self.W,0))
            self.ticker = image

            
        def draw(self, offset):
            
            if not offset % 2:
                
                W = self.display.W
                
                image = self.ticker
                image = image.crop((offset, 0, offset+W, self.H))
                image = image.tostring()
                
                address = (self.Y)*W/8
                self.display.write(image, address)
        
except: pass

if __name__ == '__main__':
    
    import sched
    
    def rss(text):
        return "<rss version='2.0'><channel><item><title>ticker</title><description>%s</description></item></channel></rss>" % text
    
    feeds = [ rss('the quick brown fox jumped over the lazy dog') ]
    
    scheduler = sched.scheduler(time.time, time.sleep)
    
    #display = pydisplay.MakeDisplay('sed1330', W=160, H=80, dev=0)
    #display = pydisplay.MakeDisplay('gu3900dma', dev=1)
    display = pydisplay.MakeDisplay('gu3900', W=256, H=64, dev=0)
    #display = pydisplay.MakeDisplay('el320_240', bus='par', dev=1)
    
    #ticker = RssTicker(scheduler, (0,40,display.W,24), display, feeds)
    ticker = RssTicker(scheduler, (0,40,display.W,24), display, feeds)
    ticker.update(feeds)
    
    scheduler.run()
    
