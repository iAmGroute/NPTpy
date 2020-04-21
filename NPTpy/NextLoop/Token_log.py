
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    AwaitPre  = (   True,      True)
    AwaitPost = (   True,      True)


LogClass = newClass('Token', Etypes, enabled=False)

