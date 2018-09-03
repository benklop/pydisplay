#!/usr/bin/python

"""
Script to play RSS feed summaries as a ticker on a Noritake T-series VFD.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import noritake
import feedparser
import time
import sched

from quote import YahooStockQuote
    
_feeds = [
    "http://seattletimes.nwsource.com/rss/home.xml",
    "http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml"
]

s = sched.scheduler(time.time, time.sleep)

def playNextRssFeed(display, feeds):

    if len(feeds) < 1: feeds = _feeds
    
    try:
        
        parse = feedparser.parse(feeds[0])
        
        display.clear()
        display.write(parse.feed.title)
        
        ticker = ' ' * 40
        
        for entry in parse.entries:
            headline = entry.title
            if entry.has_key('summary'): headline += ': ' + entry.summary
            headline = headline.encode('utf-8').replace('\n', ' ')
            ticker += headline + (' '*10)
            
        ticker  += ' ' * 30
            
        s.enter(0, 0, scrollTicker, (display, feeds, ticker))
        
    except:
        
        # if this didn't work, go on to the next feed
        s.enter(0, 0, playNextRssFeed, (display, feeds[1:]))
    
def scrollTicker(display, feeds, ticker):
    
    display.moveCursor(0,1)
    display.write(ticker[:40])
    
    if len(ticker) > 40:
        s.enter(0.12, 0, scrollTicker, (display, feeds, ticker[1:]))
    else:
        s.enter(0, 0, playNextRssFeed, (display, feeds[1:]))

#display = noritake.T20ASerial(device='/dev/ttyS0')     # /dev/ttyUSB0, COM1
#display = noritake.S20A(dev=0)
display = noritake.T20APar(dev=2)
display.setCursorMode(2)        # invisible
display.setLineEndingMode(0)    # wrap

playNextRssFeed(display, _feeds)
    
s.run()