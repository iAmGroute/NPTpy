import platform

class OS:
    linux   = 0
    mac     = 1
    windows = 2

if   platform.system() == 'Linux':   this_OS = OS.linux
elif platform.system() == 'Darwin':  this_OS = OS.mac
elif platform.system() == 'Windows': this_OS = OS.windows
