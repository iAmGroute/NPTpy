
from .Log import newClass

class Etypes:  # (Enabled, Displayed)
    Stopping   = (   True,      True)
    Stopped    = (   True,      True)
    Watching   = (  False,     False)
    Resolving  = (  False,     False)
    Continuing = (  False,     False)
    NotFound   = (   True,      True)
    Running    = (  False,     False)
    RunError   = (   True,      True)
    Finished   = (  False,     False)
    Paused     = (  False,     False)


LogClass = newClass('Loop', Etypes)

