
from LogPack import newClass

class Etypes: # (Enabled, Displayed)
    Stop      = (   True,      True)
    NewFuture = (   True,      True)
    NewEvent  = (   True,      True)
    NewQueue  = (   True,      True)
    Enqueue   = (   True,      True)
    NotFound  = (   True,      True)
    Running   = (   True,      True)
    Finished  = (   True,      True)
    RunError  = (   True,      True)
    Paused    = (   True,      True)


LogClass = newClass('Loop', Etypes, enabled=False)

