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


class Widget(object):
    
    def __init__(self, scheduler, rect):
        
        self.scheduler = scheduler
        self.schedule = self.scheduler.enter
        (self.X, self.Y, self.W, self.H) = rect
    
    def render(self):
        pass

    def refresh(self, display):
        
        image = self.render()
        
        display.bitmap((self.X,self.Y), image, fill=1)
        
    def start(self, display, interval=5):
        
        self.schedule(5,0,start,[display, interval])
        
        self.refresh(display)
        
class Clock(Widget):
    
    def __init__(self, scheduler, rect):

        Widget.__init__(self, scheduler, rect)        
        
        draw = Draw(Image.new('1', (0,0)))
        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            (w,h) = draw.textsize('12:55', self.font)
            if w < self.W: break
        
    def render(self):
        
        (W,H) = (self.W, self.H)
        image = Image.new('1', (W,H), color=0)
        draw = Draw(image)
        
        t = time.localtime()
        hour = t.tm_hour%12
        if hour == 0: hour = 12
        text = '%d:%02d' % (hour, t.tm_min)
        (w,h) = draw.textsize(text, self.font)
        draw.text((-3,-h/6), text=text, font=self.font, fill=1)
        
        return image
        
class Date(Widget):
    
    def __init__(self, scheduler, rect):

        Widget.__init__(self, scheduler, rect)        
        
        draw = Draw(Image.new('1', (0,0)))
        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            (w,h) = draw.textsize('Wednesday', self.font)
            if w < self.W: break
        
    def render(self):
        
        (W,H) = (self.W, self.H)
        image = Image.new('1', (W,H), color=0)
        draw = Draw(image)
        
        draw.text((0,1), time.strftime('%A'),       font=self.font, fill=1)
        draw.text((0,H*5/11), time.strftime('%d %b %Y'), font=self.font, fill=1)
        L = W - 93
            
        return image
        
class Mail(Widget):
    
    def __init__(self, scheduler, rect, mail=None):
        
        Widget.__init__(self, scheduler, rect)        
        
        draw = Draw(Image.new('1', (0,0)))
        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            (w,h) = draw.textsize('7', self.font)
            if w < self.W-32: break

        if mail == None: mail = gmail.GmailStatus()
        self.mail = mail
        self.mailicon = Image.open('mail.gif').convert('L').point(lambda x: 255-x, mode='1')
        
        self.update()
        
    def update(self):
    
        self.schedule(1*60, 0, self.update, [])
        thread = threading.Thread(target=self.mail.refresh)
        thread.start()
        
    def render(self):

        (W,H) = (self.W, self.H)
        image = Image.new('1', (W,H), color=0)
        draw = Draw(image)
        
        newmail = self.mail.messages
        
        if newmail > 0:
            
            draw.bitmap((0,2), self.mailicon, fill=1)
           
            text = '%d' % newmail
            (w,h) = draw.textsize(text, self.font)
            draw.text((30,(32-h)/2), text=text, font=self.font, fill=1)
            
        return image


class Weather(Widget):
    
    def __init__(self, scheduler, rect):
        
        Widget.__init__(self, scheduler, rect)        

        draw = Draw(Image.new('1', (0,0)))
        for size in xrange(100):
            self.font = ImageFont.truetype('trebuc.ttf', 100-size)
            (w,h) = draw.textsize('77', self.font)
            if w < self.W-36: break
    
        # regexes for parsing weather reports
        self.icontag = re.compile('<icon_url_name>(.+).jpg</icon_url_name>')
        self.tempftag = re.compile('<temp_f>(\d+)</temp_f>')
        
        self.update()
        
    def update(self):

        def _update(self):

            code = 'KBFI'
            url = 'http://www.nws.noaa.gov/data/current_obs/%s.xml' % ( code )
            s = urllib.urlopen(url).read()
            
            self.tempf = self.tempftag.search(s).groups(1)[0]
            self.icon = self.icontag.search(s).groups(1)[0]
        
        thread = threading.Thread(target=_update, args=[self])
        thread.start()
        
    
    def render(self):
        
        (W,H) = (self.W, self.H)
        image = Image.new('1', (W,H), color=0)
        draw = Draw(image)
            
        try:
            
            text = self.tempf
            (w,h) = draw.textsize(text, self.font)
            Y = (32-h)/2
            draw.text((30,Y), text, font=self.font, fill=1)
        
            X = 30 + w
            draw.ellipse((X-2,2,X+2,6), outline=1, fill=0)
            
            icon = Image.open(self.icon+'.gif').convert('L').point(lambda x: 255-x, mode='1')
            draw.bitmap((0,2), icon, fill=1)
            
        except: pass
        

            
        return image    


import pydisplay
import gmail

if __name__ == '__main__':
    
    scheduler = sched.scheduler(time.time, time.sleep)
    
    #display = pydisplay.MakeDisplay('gu300', dev=1, fastwrite=False)
    
    gmail = gmail.GmailStatus()
    
    #display0 = pydisplay.MakeDisplay('LCD4', W=320, H=240, dev=0)
    #Clock(scheduler, (0, 0, 160, 32)).refresh(display0)
    #Mail(scheduler, (172, 0, 64, 32), gmail).refresh(display0)
    #Weather(scheduler, (320-82, 0, 82, 32)).refresh(display0)
    #
    #display1 = pydisplay.MakeDisplay('sed1330', W=160, H=80, dev=0)
    #Clock(scheduler, (0, 0, 160, 32)).refresh(display1)
    #Mail(scheduler, (160-64, 40, 54, 32), gmail).refresh(display1)
    #Weather(scheduler, (0, 40, 80, 32)).refresh(display1)
    
    display2 = pydisplay.MakeDisplay('ks0108', W=128, H=64, dev=0)
    Clock(scheduler, (0, 0, 80, 32)).refresh(display2)
    Date(scheduler, (72, 0, 56, 32)).refresh(display2)
    Weather(scheduler, (0, 32, 76, 32)).refresh(display2)
    Mail(scheduler, (76, 32, 52, 32), gmail).refresh(display2)
    
    display3 = pydisplay.MakeDisplay('gu311', dev=0)
    Clock(scheduler, (0, 0, 72, 24)).refresh(display3)
    Date(scheduler, (72, 0, 56, 24)).refresh(display3)
    #Weather(scheduler, (0, 0, 76, 32)).refresh(display3)
    #Mail(scheduler, (76, 0, 52, 32), gmail).refresh(display3)
  
    scheduler.run()


