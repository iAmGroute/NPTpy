
from .Log import newClass

class EtypesL: # (Enabled, Displayed)
    Stop      = (   True,      True)
    NewFuture = (   True,      True)
    Enqueue   = (   True,      True)
    NotFound  = (   True,      True)
    Running   = (   True,      True)
    Finished  = (   True,      True)
    RunError  = (   True,      True)
    Paused    = (   True,      True)


LogClassL = newClass('Loop', EtypesL)


class EtypesF: # (Enabled, Displayed)
    Ready     = (   True,      True)
    Cancel    = (   True,      True)
    Reset     = (   True,      True)
    Await     = (   True,      True)


LogClassF = newClass('Future', EtypesF)

