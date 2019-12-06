
from Common.Log import newClass

class Etypes:     # (Enabled, Displayed)
    Inited        = (   True,      True)
    Deleted       = (   True,      True)
    NewConnection = (   True,      True)
    Accept        = (   True,      True)
    Decline       = (   True,      True)


LogClass = newClass('Listener', Etypes)

