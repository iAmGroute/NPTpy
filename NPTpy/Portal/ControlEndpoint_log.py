
from Common.Log import newClass

class Etypes:      # (Enabled, Displayed)
    Inited         = (   True,      True)
    Deleted        = (   True,      True)
    Corrupted      = (   True,      True)
    SendingKA      = (   True,      True)
    ReceivedKA     = (   True,      True)
    Created        = (   True,      True)
    ReadyToAccept  = (   True,      True)
    DeletedByOther = (   True,      True)
    DeletedByUs    = (   True,      True)


LogClass = newClass('ControlEndpoint', Etypes)

