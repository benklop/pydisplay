#!/usr/bin/python

"""
Example script to retrieve Google mail inbox status.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import time
import urllib2
import re

USERNAME = 'username'
PASSWORD = 'password'

POLL_DELAY = 60

class GmailStatus(object):
    
    def __init__(self):
        
        # prepare credentials for gmail access
        x = urllib2.HTTPPasswordMgrWithDefaultRealm()
        x.add_password(None, 'https://mail.google.com', USERNAME, PASSWORD)
        auth = urllib2.HTTPBasicAuthHandler(x)
        opener = urllib2.build_opener(auth)
        urllib2.install_opener(opener)
        
        # build a regex to parse the Atom results
        self.regex = re.compile(r'<fullcount>(\d+)</fullcount>')
        
        self.messages = 0
        
    def refresh(self):

        try:        
            feed = urllib2.urlopen('https://mail.google.com/mail/feed/atom')
            s = feed.read()
    
            # find the value of the <fullcount> element        
            nMessages = self.regex.search(s).groups(1)
            self.messages = int(nMessages[0])
        except: pass
                
from widget import Alert

import Image
from ImageDraw import ImageDraw, Draw
import ImageFont

import threading

class GmailAlert(Alert):
    
    def __init__(self, scheduler, display):
        
        Alert.__init__(self, scheduler, display)
        
        self.newmail = 0
        self.mail = GmailStatus()
        
    def update(self):

        def _update(self):
            
            try:
                self.mail.refresh()
                
                oldmail = self.newmail
                self.newmail = self.mail.messages
                
                if self.newmail > oldmail:
                    
                    self.schedule(0,0,self.alert,[5])
                    
            except:
                print 'mail thread crashed'
            
        thread = threading.Thread(target=_update, args=[self])
        thread.start()
        
    def alert(self, interval=5):
        
        if self.newmail > 0:
            
            super(GmailAlert, self).alert(interval)
            
    def render(self, draw):
        
        W, H = self.display.W, self.display.H
        
        text = 'you have %d new messages' % self.newmail
        if self.newmail == 1: text = 'you have 1 new message'
        
        font = None
        (w,h) = (0,0)
        
        for size in xrange(100):
            font = ImageFont.truetype('trebuc.ttf', 100-size)
            (w,h) = font.getsize(text)
            if w < W - 36: break
            
        draw.text((h+6,(H-h)/2), text, font=font, fill=1)

        self.icon = Image.open('mail.gif').resize((h,h))
        draw.bitmap((0,(H-h)/2), self.icon, fill=1)


