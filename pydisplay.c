#include <linux/ppdev.h>
#include <linux/parport.h>
#include <sys/ioctl.h>

#include <stdio.h>

void gu3900_write(int fd, char* data, int len)
{
    // for each byte in the input sequence
    int i = 0;
    for (; i < len; ++i)
    {
        // write this byte to the data pins
        char d = data[i];
        ioctl(fd, PPWDATA, &d);
                        
        // wait for RDY
        int status = PARPORT_STATUS_BUSY;
        do {
            ioctl(fd, PPRSTATUS, &status);
        } while (status & PARPORT_STATUS_BUSY);

        // toggle WR
        struct ppdev_frob_struct frob = { PARPORT_CONTROL_STROBE, 0 };
        frob.val  = PARPORT_CONTROL_STROBE;
        ioctl(fd, PPFCONTROL, &frob);
        frob.val = 0;
        ioctl(fd, PPFCONTROL, &frob);
    }
}

#include <time.h>

void ndelay(int delay)
{
    int spin = 0;
    while (spin++ < delay/4) {}
}

#define ndelay(x)

int _delay = 0;//1000;// * 1000;

void sed1330_command(int fd, char cmd)
{   
    struct ppdev_frob_struct frob = { 0, 0 };

    // set CS = 0
    frob.mask = PARPORT_CONTROL_INIT;
    frob.val  = 0;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);

    // set A0 = 1
    frob.mask = PARPORT_CONTROL_SELECT;
    frob.val  = 0;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);
    
    // write this byte to the data pins
    char arg = cmd;
    ioctl(fd, PPWDATA, &arg);
    ndelay(_delay);
                    
    // toggle WR
    frob.mask = PARPORT_CONTROL_STROBE;
    frob.val  = PARPORT_CONTROL_STROBE;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);
    
    frob.val = 0;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);
}

void sed1330_write(int fd, char* data, int len)
{
    struct ppdev_frob_struct frob = { 0, 0 };
    
    // set CS = 0
    frob.mask = PARPORT_CONTROL_INIT;
    frob.val  = 0;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);

    // set A0 = 0
    frob.mask = PARPORT_CONTROL_SELECT;
    frob.val  = PARPORT_CONTROL_SELECT;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);
    
    // for each byte in the input sequence
    int i = 0;
    for (; i < len; ++i)
    {
        // write this byte to the data pins
        char arg = data[i];
        ioctl(fd, PPWDATA, &arg);
        ndelay(_delay);
        
        // toggle WR
        frob.mask = PARPORT_CONTROL_STROBE;
        frob.val  = PARPORT_CONTROL_STROBE;
        ioctl(fd, PPFCONTROL, &frob);
        ndelay(_delay);
        
        frob.val = 0;
        ioctl(fd, PPFCONTROL, &frob);
        ndelay(_delay);
    }
}

void gu300_write(int fd, char* data, int len)
{
    struct ppdev_frob_struct frob = { 0, 0 };
    
    // set CS = 0
    frob.mask = PARPORT_CONTROL_AUTOFD;
    frob.val  = PARPORT_CONTROL_AUTOFD;
    ioctl(fd, PPFCONTROL, &frob);
    ndelay(_delay);
    
    // for each byte in the input sequence
    int i = 0;
    for (; i < len; ++i)
    {
        // write this byte to the data pins
        char arg = data[i];
        ioctl(fd, PPWDATA, &arg);
        ndelay(_delay);
        
        // toggle WR
        frob.mask = PARPORT_CONTROL_STROBE;
        frob.val  = PARPORT_CONTROL_STROBE;
        ioctl(fd, PPFCONTROL, &frob);
        ndelay(_delay);
        
        frob.val = 0;
        ioctl(fd, PPFCONTROL, &frob);
        ndelay(_delay);
    }    
}

