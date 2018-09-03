from distutils.core import setup, Extension
import sys

if sys.platform == 'linux2':
    ext_modules = [ Extension('_pydisplay',sources=['pydisplay.c']) ]
else:
    ext_modules = []
    
setup(name='pydisplay',                                                   \
    ext_modules=ext_modules,      \
    py_modules=[ 'noritake', 'gu311', 'gu300', 'gu3900', 'gu3900dma', 'gu7000',\
                 't20a', 's20a', 'sed1330', 'sed1520', 't6963c',          \
                 'ftdi', 'planar', 'lcd', 'babcock', 'ubw', 'ks0108', 'pydisplay' ])

