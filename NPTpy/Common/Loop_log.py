
from .Log import newClass

class Etypes:  # (Enabled, Displayed)
    Stopping   = (   True,      True)
    Stopped    = (   True,      True)
    Watching   = (  False,     False)
    Resolving  = (  False,     False)
    NotFound   = (   True,      True)
    Enqueue    = (  False,     False)
    Running    = (  False,     False)
    RunError   = (   True,      True)
    Finished   = (  False,     False)
    Paused     = (  False,     False)


LogClass = newClass('Loop', Etypes)

