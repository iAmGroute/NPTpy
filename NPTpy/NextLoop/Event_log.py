
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Call      = (   True,      True)
    Await     = (   True,      True)
    Resolve   = (   True,      True)
    NewToken  = (   True,      True)
    Reset     = (   True,      True)

LogClass = newClass('Event', Etypes)

