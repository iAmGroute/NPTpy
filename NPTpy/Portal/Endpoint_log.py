
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Inited    = (   True,      True)
    Deleted   = (   True,      True)
    Removing  = (   True,      True)
    Finishing = (   True,      True)


LogClass = newClass('Endpoint', Etypes)

