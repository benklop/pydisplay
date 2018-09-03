
import gu7000
d = gu7000.GU7000Ser(140, 16)

import gmail
mail = gmail.GmailStatus()


def run():
    
    import random
    import time

    x,y = 70,8
    
    while True:
        
        mail.refresh()
        
        for i in xrange(1):#20):
            
            msgs = mail.messages
            
            if (msgs > 0):
    
                d.clearDisplay()
                time.sleep(1)
                
                d.setBrightness(100)
                if msgs>9: s=2
                elif msgs>1: s=1
                else: s=0
                d.setCursor([7,3,0][s], msgs%2)
                d.write('you have %d message%c' % (msgs, ' ss'[s]) )
                time.sleep(2)
                
            else:
                
                for j in xrange(3*4):
                    
                    dx = random.randint(-1,1);
                    x += dx
                    x = min(x,139); x = max(x,0)
                    if (not dx):
                        y += random.randint(-1,1);
                        y = min(y,15); y = max(y,0)
                    
                    d.clearDisplay()
                    d.setBrightness(20)
                    d.setCursor(x, y/8)
                    d.displayBitImage( 1, 1, chr(0x80>>(y%8)) )
                    time.sleep(0.25)
                
if __name__ == '__main__':
    
    run()
        
