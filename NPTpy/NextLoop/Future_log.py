
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Ready     = (   True,      True)
    Cancel    = (   True,      True)
    Reset     = (   True,      True)
    Await     = (   True,      True)
    NewToken  = (   True,      True)


LogClass = newClass('Future', Etypes, enabled=False)

