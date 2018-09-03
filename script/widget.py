#!/usr/bin/python

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

import time
import sched
import re
import urllib
import threading


class Alert(object): 

    def __init__(self, scheduler, display):
        
        assert scheduler
        assert display
        
        self.display   = display
        self.scheduler = scheduler
        self.schedule  = scheduler.enter
        
    def start(self):
        
        self.schedule(1*60, 0, self.start, [])
        self.update()
        
    def alert(self, interval=10):

        (W,H) = (self.display.W, self.display.H)
        image = Image.new('1', (W,H))
        draw = Draw(image)
        
        self.render(draw)
        
        self.display.bitmap((0,0), image, fill=1)
        time.sleep(interval)
        self.display.clear()
        
    def update(self): pass # override to implement
        
    def render(self, draw): pass # override to implement
        
class Widget(object):
    
    def __init__(self, scheduler, rect):
        
        assert scheduler
        
        self.scheduler = scheduler
        self.schedule = self.scheduler.enter
        (self.X, self.Y, self.W, self.H) = rect
    
    def render(self, draw): pass # override to implement

    def refresh(self, display):
        
        (W,H) = (self.W, self.H)
        image = Image.new('1', (W,H))
        draw = Draw(image)
        
        self.render(draw)
        
        display.bitmap((self.X,self.Y), image, fill='#fff')
        
    def start(self, display, interval=5):
        
        self.schedule(interval,0,self.start,[display, interval])
        
        self.refresh(display)


class Template(Widget):
    def __init__(self, point, imagefile):
        self.X, self.Y = point
        self.image = Image.open(imagefile)
        self.W, self.H = self.image.size
        
    def render(self, draw):
        draw.bitmap((0,0), self.image, fill=1)
        
        
class Clock(Widget):
    
    def __init__(self, scheduler, rect):

        Widget.__init__(self, scheduler, rect)        
        
        for size in xrange(100,0,-1):
            self.font = ImageFont.truetype('trebuc.ttf', size)
            l,t,r,b = self.font.getmask('0123456789', '1').getbbox()
            if (b-t) < self.H: break
        
    def render(self, draw):
        
        t = time.localtime()
        hour = t.tm_hour%12
        if hour == 0: hour = 12
        text = '%d:%02d' % (hour, t.tm_min)
        l,t,r,b = self.font.getmask(text, '1').getbbox()
        self.W,self.H = (r-l), (b-t)
        draw.text((-l,-t), text=text, font=self.font, fill=1)
        
        
class Date(Widget):
    
    def __init__(self, scheduler, rect):

        Widget.__init__(self, scheduler, rect)        
        
        for size in xrange(100):
            self.font = ImageFont.truetype('DejaVuSans.ttf', 100-size)
            (w,h) = self.font.getsize('27 Www 2077')
            if w < self.W: break
        
    def render(self, draw):
        
        (a,d) = self.font.getmetrics()
        draw.text((0,d/2), time.strftime('%A'), font=self.font, fill=1)
        draw.text((0,self.H*5/11), time.strftime('%d %b %Y'), font=self.font, fill=1)
            
        
class Mail(Widget):
    
    def __init__(self, scheduler, rect, mail=None):
        
        Widget.__init__(self, scheduler, rect)        
        
        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            l,t,r,b = self.font.getmask('0123456789', '1').getbbox()
            if (b-t) < self.H: break

        if mail == None: mail = gmail.GmailStatus()
        self.mail = mail
        self.icon = Image.open('mail.gif').resize((self.H,self.H))
        
        self.update()
        
    def update(self):
    
        self.schedule(1*60, 0, self.update, [])
        thread = threading.Thread(target=self.mail.refresh)
        thread.start()
        
    def render(self, draw):

        newmail = self.mail.messages
        
        if newmail > 0:
            
            draw.bitmap((0,0), self.icon, fill=1)
           
            text = '%d' % newmail
            l,t,r,b = self.font.getmask(text, '1').getbbox()
            draw.text((self.H+2,-t), text=text, font=self.font, fill=1)
            self.W = self.H + 6 + (r-l)
            self.H = b-t
            

class Weather(Widget):
    
    def __init__(self, scheduler, rect):
        
        Widget.__init__(self, scheduler, rect)        

        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            l,t,r,b = self.font.getmask('0123456789', '1').getbbox()
            if (b-t) < self.H: break
    
        # regexes for parsing weather reports
        self.icontag = re.compile('<icon_url_name>(.+).jpg</icon_url_name>')
        self.tempftag = re.compile('<temp_f>(\d+)</temp_f>')
        
        self.update()
        
    def update(self):

        self.schedule(1*60, 0, self.update, [])

        def _update(self):
            
            try:
                code = 'KBFI'
                url = 'http://www.nws.noaa.gov/data/current_obs/%s.xml' % ( code )
                s = urllib.urlopen(url).read()
                
                self.tempf = self.tempftag.search(s).groups(1)[0]
                self.icon = self.icontag.search(s).groups(1)[0]
            except:
                print 'weather thread crashed'
        
        thread = threading.Thread(target=_update, args=[self])
        thread.start()
        
    
    def render(self, draw):

        X = 0
        
        try:
            
            icon = Image.open(self.icon+'.gif').resize((self.H,self.H)).convert('L').point(lambda x: 255-x, mode='1')
            draw.bitmap((X,0), icon, fill=1)
            X = self.H
            
        except: pass
        
        try:
            text = self.tempf
            (w,h) = self.font.getsize(text)
            l,t,r,b = self.font.getmask(text, '1').getbbox()
            draw.text((X,-t), text, font=self.font, fill=1)
            self.H = b-t
            X += 6+r-l
            
            draw.ellipse((X,0,X+4,4), outline=1, fill=0)
            X += 8
            
        except: pass
        
        self.W = X
        

import pydisplay
import gmail

if __name__ == '__main__':
    
    scheduler = sched.scheduler(time.time, time.sleep)
    
    #display = pydisplay.MakeDisplay('gu300', dev=1, fastwrite=False)
    
    gmail = gmail.GmailStatus()
    
    #display0 = pydisplay.MakeDisplay('LCD4', W=320, H=240, dev=0)
    #Clock(scheduler, (0, 0, 160, 40)).start(display0)
    #Mail(scheduler, (172, 0, 64, 40), gmail).start(display0)
    #Weather(scheduler, (320-82, 0, 82, 40)).start(display0)
    #
    #display = pydisplay.MakeDisplay('sed1330', W=160, H=80, dev=0)
    #Clock(scheduler, (0, 0, 0, 36)).start(display)
    #Date(scheduler, (112, 0, 48, 36)).start(display)
    #Weather(scheduler, (0, 40, 0, 36)).start(display)
    #Mail(scheduler, (160-64, 40, 0, 36), gmail).start(display)
    
    display = pydisplay.MakeDisplay('ks0108', W=128, H=64, dev=0)
    Clock(scheduler, (0, 0, 0, 30)).start(display)
    Date(scheduler, (80, 0, 48, 30)).start(display)
    Weather(scheduler, (0, 34, 0, 30)).start(display)
    Mail(scheduler, (76, 34, 0, 30), gmail).start(display)
    
    #display3 = pydisplay.MakeDisplay('gu311', dev=0)
    #Clock(scheduler, (0, 0, 72, 24)).start(display3)
    #Date(scheduler, (72, 0, 56, 24)).start(display3)
    #Weather(scheduler, (0, 0, 76, 32)).start(display3)
    #Mail(scheduler, (76, 0, 52, 32), gmail).start(display3)
  
    scheduler.run()


