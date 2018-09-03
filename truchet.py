"""
A visualization to test refresh performance.

Copyright (c) 2006 spacemarmot@users.sourceforge.net

This file is released under the GNU Lesser General Public Licence.
See the file LICENSE for details.
"""


import Image
import pydisplay
import random
import time


def Truchet(display,W,H):
    
    # define some truchet tile patterns
    pattern = '\x08\x04\x02\x01\x80\x40\x20\x10'
    squaretile = ( pattern, pattern[::-1] )
    pattern = '\x08\x08\x04\x03\xc0\x20\x10\x10'
    roundtile = ( pattern, pattern[::-1] )
    binary = ( '\x00\x10\x10\x10\x10\x10\x10\x00', '\x00\x18\x24\x24\x24\x24\x18\x00' )
    dots0  = ( '\x00\x00\x00\x18\x18\x00\x00\x00', '\x00\x00\x18\x3c\x3c\x18\x00\x00' )
    dots1  = ( '\x00\x06\x06\x00\x00\x00\x00\x00', '\x06\x0F\x0F\x06\x00\x00\x00\x00' )
    dots2  = ( '\x00\x00\x00\x00\x00\x06\x06\x00', '\x00\x00\x00\x00\x06\x0F\x0F\x06' )
    dots3  = ( '\x00\x60\x60\x00\x00\x00\x00\x00', '\x60\xF0\xF0\x60\x00\x00\x00\x00' )
    dots4  = ( '\x00\x00\x00\x00\x00\x60\x60\x00', '\x00\x00\x00\x00\x60\xF0\xF0\x60' )
    empty  = ( '\x00\x00\x00\x00\x00\x00\x00\x00', '\x01\x00\x00\x00\x00\x00\x00\x00' )
    
    # build a table of screen addresses
    addr = [ (x,y) for x in xrange(0,W,8) for y in xrange(0,H,8) ]

    # build a table of tile pattern selections
    choice = [0,1,2,3,4,5,6,7]
        
    while 1:
        random.shuffle(choice)
        for c in choice:
            # pick a random tile pattern from the available patterns
            pattern = [binary, dots0, dots1, dots2, dots3, dots4, roundtile, squaretile][c]

            # for each (randomized) address location
            random.shuffle(addr)
            for a in addr * random.randint(1,3):
                
                # draw a random tile 
                tile = random.choice(pattern)
                image = Image.fromstring('1', (8,8), tile)
                display.bitmap(a, image)
                time.sleep(0)
                
            for a in addr * random.randint(0,1):
                image = Image.fromstring('1', (8,8), empty[0])
                display.bitmap(a, image)
            
if __name__ == '__main__':
    #draw = pydisplay.MakeDisplay('el320_240', dev=3, bus='par')
    #draw = pydisplay.MakeDisplay('EL640_200SK', dev=2, bus='par')
    #draw = pydisplay.MakeDisplay('LCD4', 320, 240, dev=3, bus='par')
    #draw = pydisplay.MakeDisplay('sed1330', W=160, H=80, dev=1, bus='par')
    #draw = pydisplay.MakeDisplay('sed1330', W=160, H=80, dev=0, bus='usb')
    #draw = pydisplay.MakeDisplay('ks0108', W=128, H=64, dev=0, bus='usb')
    #draw = pydisplay.MakeDisplay('gu311', dev=1)
    #draw = pydisplay.MakeDisplay('gu7000', dev=0)
    #draw = pydisplay.MakeDisplay('gd120c280', dev=0)
    #draw = pydisplay.MakeDisplay('gu3900', W=256, H=64, dev=1)
    #draw = pydisplay.MakeDisplay('gu3900dma', W=256, H=64, dev=1)
    draw = pydisplay.MakeDisplay('gu300', W=256, H=64, dev=2)
    #draw = pydisplay.MakeDisplay('t6963c', W=128, H=64, dev=0)
    #draw = pydisplay.MakeDisplay('sed1520', dev=0)
    
    W = draw.display.W
    H = draw.display.H
    Truchet(draw, W, H)

