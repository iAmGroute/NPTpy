
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Stop      = (   True,      True)
    NewFuture = (  False,     False)
    NewEvent  = (  False,     False)
    NewQueue  = (  False,     False)
    Enqueue   = (  False,     False)
    NotFound  = (   True,      True)
    Running   = (  False,     False)
    Finished  = (  False,     False)
    RunError  = (   True,      True)
    Paused    = (  False,     False)


LogClass = newClass('Loop', Etypes, enabled=True)

