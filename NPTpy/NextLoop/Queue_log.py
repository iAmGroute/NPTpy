
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Aenter    = (   True,      True)
    Aexit     = (   True,      True)
    Cancel    = (   True,      True)


LogClass = newClass('Queue', Etypes, enabled=False)

