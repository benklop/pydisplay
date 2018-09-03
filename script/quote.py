"""
Script to show current time, weather, and rss feeds
on a variety of graphics displays.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""

import urllib

class YahooStockQuote:
    
    def __init__(self, *symbols):
        
        self.symbols = symbols
        
    def read(self):

        result = '<rss version="2.0"><channel><title>Yahoo! Stock Quotes</title>'
        
        for symbol in self.symbols:
            
            url = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=l1c1' % symbol
            f = urllib.urlopen(url)
            quote = f.read().strip().split(',')
            f.close()
            result += '<item><title>%s</title>' % symbol
            result += '<description>%s (%s)</description></item>' % (quote[0], quote[1])
                
        result += '</channel></rss>'
            
        return result