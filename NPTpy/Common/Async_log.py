
from .Log import newClass

class Etypes:  # (Enabled, Displayed)
    Inited     = (   True,      True)
    Deleting   = (   True,      True)
    Reset      = (   True,      True)
    Attach     = (   True,      True)
    Detach     = (   True,      True)
    Fire       = (   True,      True)
    FireResult = (   True,      True)


LogClass = newClass('Promise', Etypes, enabled=False)

