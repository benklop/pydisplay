import Image
from ImageDraw import ImageDraw, Draw
import ImageFont

import os
import platform

tuxicon = Image.open('tux.jpg')

font20 = ImageFont.truetype('DejaVuSans.ttf', 20)
font16 = ImageFont.truetype('DejaVuSans.ttf', 16)
font9  = ImageFont.truetype('DejaVuSans.ttf', 9)
#tinyfont = ImageFont.truetype('TINY.TTF', 6)

def drawPieChart(draw, xy, title, format, value, max=100, min=0):

    x,y = xy
    
    try:
        text = format % (value, max-min)
    except:
        text = format % value
        
    draw.text((x+30,y+6), text=text, font=font20, fill=0xff)
    draw.text((x+30,y-2), text=title, font=font9, fill=0xff)
    
    end = 360 - (360 * (value-min) / (max-min))
    draw.arc((x,y,x+24,y+24), start=0, end=360, fill=0xff)
    draw.pieslice((x,y,x+24,y+24), start=end, end=360, fill=0xff, outline=1)
                 
                 
def drawBarChart(draw, xy, title, format, value, max=100, min=0):

    x,y = xy
    
    try:
        text = format % (value, max-min)
    except:
        text = format % value
        
    draw.text((x+16,y+6), text=text, font=font20, fill=0xff)
    draw.text((x+16,y-2), text=title, font=font9, fill=0xff)
    
    level = 24 - (value-min) * 24 / (max - min)
    if level > 24: level = 24
    if level < 0: level = 0
    draw.rectangle((x,y,x+8,y+24), fill=0, outline=1)
    draw.rectangle((x,y+level,x+8,y+24), fill=1, outline=0xff)
    
from widget import Widget


   
class CpuType(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(CpuType, self).__init__(scheduler, rect)
        
        self.icon = Image.open('amd.jpg')
        
        cpuinfo = open('/proc/cpuinfo').readlines()
        model = cpuinfo[4].split(':')
        self.model = model[1].strip()
    
    def refresh(self, draw):
        
        def getCpuSpeed():
            
            cpuinfo = open('/proc/cpuinfo').readlines()
            speed = cpuinfo[6].split(':')
            speed = speed[1].strip()
            
            return speed
        
        x = self.X
        y = self.Y-3
        draw.bitmap((x,y), self.icon, fill=1)
        
        text = '%s' % (self.model)
        draw.text((x+40,y), text=text, font=font16, fill=1)
    
        speed = getCpuSpeed()
        text = '%d MHz' % (float(speed))
        draw.text((x+40,y+16), text=text, font=font16, fill=1)        

class LoadAvg(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(LoadAvg, self).__init__(scheduler, rect)
        
    def refresh(self, draw):
        
        def getLoadAvg():
            
            loadavg = open('/proc/loadavg').read().split()
            loadavg = float(loadavg[0])
            return loadavg

        loadavg = getLoadAvg()
        drawBarChart(draw, (self.X,self.Y), 'load avg  ', '%.2f', loadavg, 2)        

class CpuBusy(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(CpuBusy, self).__init__(scheduler, rect)
        
        self.user = 0
        self.nice = 0
        self.sys  = 0
        self.idle = 0
        
    def refresh(self, draw):
        
        def getCpuBusy():
            
            f = open('/proc/stat')
            stat = f.readline().split()
            f.close()
            
            user = float(stat[1]) - self.user
            nice = float(stat[2]) - self.nice
            sys  = float(stat[3]) - self.sys
            idle = float(stat[4]) - self.idle
            
            self.user = float(stat[1])
            self.nice = float(stat[2])
            self.sys  = float(stat[3])
            self.idle = float(stat[4])
            
            try:
                used = 100 * (user+nice+sys) / (user+nice+sys+idle)
            except:
                used = 0
            
            return used
        
        busy = getCpuBusy()
        drawPieChart(draw, (self.X,self.Y), 'cpu busy  ', '%d%%', busy)        


class CpuTemp(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(CpuTemp, self).__init__(scheduler, rect)
        
    def get(self):
        
        temp = open('/proc/acpi/thermal_zone/THRM/temperature').read().split(':')
        temp = temp[1].split('C')
        temp = int(temp[0].strip())
        critical = open('/proc/acpi/thermal_zone/THRM/trip_points').readline().split(':')
        critical = critical[1].split('C')
        critical = int(critical[0].strip())
        
        return (temp, critical)
        
    def refresh(self, draw):
    
        (temp, critical) = self.get()
        drawBarChart(draw, (self.X,self.Y), 'cpu temp  ', '%d C', temp, critical, 15)

class MemFree(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(MemFree, self).__init__(scheduler, rect)
        
    def render(self, draw):
        
        (used, free, total) = self.get()
        drawPieChart(draw, (0,0), 'mem free (MB)  ', '%d/%d', free, total)
        
    def get(self):
        
        f = os.popen('free -m | grep "Mem:"')
        mem = f.read().split()
        f.close()
    
        total = int(mem[1])
        used  = int(mem[2])
        free  = int(mem[3])
        return (used, free, total)

class SwapFree(Widget):
    
    def __init__(self, scheduler, rect):
        
        super(SwapFree, self).__init__(scheduler, rect)
        
    def render(self, draw):
        
        (used, free, total) = self.get()
        
        if used > 0:
            
            text = 'swap free : %d / %d MB  ' % (free, total)
            draw.text((0,0), text=text, font=font9, fill=0xFF)
            
            w = self.W - 8        
            draw.rectangle((0,12,w,16), fill=0, outline=1)
            draw.rectangle((0,12,used*w/total,16), fill=1, outline=1)   
        
    def get(self):
        
        f = os.popen('free -m | grep "Swap:"')
        mem = f.read().split()
        f.close()
    
        total = int(mem[1])
        used  = int(mem[2])
        free  = int(mem[3])
        return (used, free, total)

class DiscFree(Widget):
    
    def __init__(self, scheduler, rect, dev):
        
        super(DiscFree, self).__init__(scheduler, rect)
        
        self.dev = dev
        self.update()
        
    def update(self):

        (self.used, self.free, self.total) = self.get()
        
    def render(self, draw):

        drawPieChart(draw, (0,0), self.dev + ' used', '%d / %d GB', self.used, self.total)
        
    def get(self):
        
        f = os.popen('df -B1G %s' % self.dev)
        f.readline()
        disk = f.read().split()
        f.close()
    
        dev   = disk[0]
        total = int(disk[1])
        used  = int(disk[2])
        free  = int(disk[3])
        
        return (used, free, total)
        
class DF(Widget):

    def __init__(self, scheduler, rect):
        
        super(DF, self).__init__(scheduler, rect)
        
        self.stat = []
        
    def update(self):
        
        self.stat = []

        f = os.popen('df -B1G -x tmpfs -x usbfs')
        
        try:
            f.readline()
            
            while True:
                d = f.readline()
                d = d.split()
                
                total = int(d[1])
                used  = int(d[2])
                free  = int(d[3])
                mount = d[5]
                
                self.stat.append( (used, free, total, mount) )                
                
        except: pass
        
        f.close()
            
        
    def render(self, draw):

        y = 0
        w = self.W - 8
        
        for s in self.stat:
            
            (used, free, total, mount) = s
            
            text = '%s  ' % mount
            draw.text((0,y), text=text, font=font9, fill=0xFF)
            
            text = ': %d / %d GB free  ' % (free, total)
            draw.text((70,y), text=text, font=font9, fill=0xFF)
            
            draw.rectangle((0,y+12,w,y+16), fill=0, outline=1)
            draw.rectangle((0,y+12,used*w/total,y+16), fill=1, outline=1)            
            
            y += 20
        
    def get(self):
        
        f = os.popen('df -B1G -x tmpfs -x usbfs')
        f.readline()
        disk = f.read().split()
        f.close()