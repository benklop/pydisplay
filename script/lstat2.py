"""
Script to show Linux system stats on a Noritake GU3900

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import Image
from ImageDraw import ImageDraw, Draw
import ImageFont

import os
import platform
import random

from widget import Widget

INTERVAL = 8

import time
import sched
scheduler = sched.scheduler(time.time, time.sleep)

font20 = ImageFont.truetype('DejaVuSans.ttf', 20)
font16 = ImageFont.truetype('DejaVuSans.ttf', 16)
font9  = ImageFont.truetype('DejaVuSans.ttf', 9)

import pydisplay
display = pydisplay.MakeDisplay('el320_240', dev=2, bus='par')
#display = pydisplay.MakeDisplay('el640_200SK', dev=2, bus='par')

from widget import Widget
import gmail
import threading

class Mail(Widget):

    def __init__(self, scheduler, rect, mail=None):
        
        Widget.__init__(self, scheduler, rect)        
        
        if mail == None: mail = gmail.GmailStatus()
        self.mail = mail
        self.icon = Image.open('mail.gif').resize((self.H,self.H))
        
        self.update()
        
        self.mail.messages = 666
        
    def update(self):
    
        self.schedule(1*60, 0, self.update, [])
        thread = threading.Thread(target=self.mail.refresh)
        thread.start()
        
    def render(self, draw):

        newmail = self.mail.messages
        if newmail > 0:
            
            text = 'you have %d new messages' % newmail
            if newmail == 1: text = 'you have 1 new message'
            
            font = None
            (w,h) = (0,0)
            
            for size in xrange(100):
                font = ImageFont.truetype('trebuc.ttf', 100-size)
                (w,h) = font.getsize(text)
                if w < self.W - (self.H+8): break
                
            draw.text((self.H+8,(self.H-h)/2), text, font=font, fill=1)
    
            self.icon = Image.open('mail.gif').resize((self.H,self.H))
            draw.bitmap((0,0), self.icon, fill=1)
            
            del font

            
mail = Mail(scheduler, (0,0,320,33))
def showMail():

    if mail.mail.messages > 0:
        
        (W,H) = (display.W, display.H)
        image = Image.new('1', (W,H))
        draw = Draw(image)

        top = random.randint(1,200)
        mail.Y = top        
        mail.refresh(draw)
        
        display.bitmap((0,0), image)
        time.sleep(INTERVAL)
        

def getIpAddr():
    
    ipaddr = os.popen('/sbin/ifconfig eth0 | grep "inet addr"')
    ipaddr = ipaddr.read().split()
    ipaddr = ipaddr[1].split(':')[1]
    
    return ipaddr

def getUptime():
    
    uptime = open('/proc/uptime')
    uptime = uptime.read().split()
    uptime = float(uptime[0])

    minutes = uptime / 60
    hours   = minutes / 60
    days    = int(hours / 24)

    hours   = int(hours % 24)
    minutes = int(minutes % 60)
    
    return (days, hours, minutes)


from widget import Template

tuxicon = Template((0,0), 'tux.jpg')

def showHost():
    
    (W,H) = (display.W, display.H)
    image = Image.new('1', (W,H))
    draw = Draw(image)
    
    top = random.randint(1,170)

    tuxicon.Y = top
    tuxicon.refresh(draw)
    
    hostname = platform.node()
    ipaddr = getIpAddr()
    text = '%s %s' % (hostname, ipaddr)
    (w,h) = draw.textsize(text, font16)
    draw.text((80,top+0), text=text, font=font16, fill=111)
    
    text = '%s %s' % (platform.system(), platform.release())
    (w,h) = draw.textsize(text, font16)
    draw.text((80,top+20), text, font=font16, fill=111)

    (days, hours, minutes) = getUptime()
    text = 'uptime %dd %dh %dm' % (days, hours, minutes)
    (w,h) = draw.textsize(text, font16)
    draw.text((80,top+40), text, font=font16, fill=111)
   
    display.bitmap((0,0), image)
    
    time.sleep(INTERVAL)

from linuxstat import CpuType, LoadAvg, CpuBusy, CpuTemp

top = 1
cputype = CpuType(scheduler, (  0,top,200,32))

loadavg = LoadAvg(scheduler, (  8,top,80,32))
cpubusy = CpuBusy(scheduler, (110,top,80,32))
cputemp = CpuTemp(scheduler, (220,top,80,32))

from linuxstat import MemFree, SwapFree, DF

memfree  = MemFree( scheduler, (0,top+0,160,40))
swapfree = SwapFree(scheduler, (0,top+32,160,40))
diskfree = DF(scheduler, (160,top,160,120))
    
def showProc():
    
    #
    # reduce screen burn in by using some of the real estate to move
    # the image around
    #
    
    top = random.randint(1,100)
    cputype.Y = top
    
    top += 40
    loadavg.Y = top
    cpubusy.Y = top
    cputemp.Y = top
    
    top += 40
    memfree.Y  = top + 0
    swapfree.Y = top + 32
    diskfree.Y = top
    
    diskfree.update()
    
    #
    # for each sample in the interval
    #
    
    for moment in xrange(INTERVAL):
        
        #
        # refresh the indicators
        #
        
        (W,H) = (display.W, display.H)
        image = Image.new('1', (W,H))
        draw = Draw(image)
    
        cputype.refresh(draw)
        loadavg.refresh(draw)
        cpubusy.refresh(draw)
        cputemp.refresh(draw)
        
        memfree.refresh(draw)
        swapfree.refresh(draw)
       
        diskfree.refresh(draw)
        
        display.bitmap((0,0), image, fill='#fff')
        
        #image.save('proc.png')
        
        time.sleep(1)

    
def isMonitorOn():
    
    result = True
    try:
        on = os.popen('xset -q | grep "Monitor is Off"')
        on = on.read()
        result = len(on) == 0
    finally:
        return result

  
Px = random.randint(0,display.W)
Py = random.randint(0,display.H)
def randomPenguin(interval=0):

    global Px, Py
    
    penguin = Image.open('tux.jpg')
    _,_,w,h = penguin.getbbox()
    
    for i in xrange(interval*2):
        
        (W,H) = (display.W, display.H)
        image = Image.new('1', (W,H))
        
        draw = Draw(image)
        Px += random.randint(-2,2)
        Px = max(Px,0); Px = min(Px,W-w)
        Py += random.randint(-2,2)
        Py = max(Py,0); Py = min(Py,H-h)
        draw.bitmap((Px,Py), penguin, fill=1)
        
        display.bitmap((0,0), image)
        time.sleep(0.5)
    
def showStats(s):
   
    if isMonitorOn():
        if mail.mail.messages > 0:
            showMail()
        else:
            showHost()
        showProc()
    else:
        showMail()
        randomPenguin(2*INTERVAL)
    
    s.enter(0,0,showStats,[s])


def run():
    
    showStats(scheduler)

    scheduler.run()
    
if __name__ == '__main__':

    run()