
from LogPack import newClass

class Etypes:      # (Enabled, Displayed)
    Inited         = (   True,      True)
    Deleted        = (   True,      True)
    Corrupted      = (   True,      True)
    SendingKA      = (  False,     False)
    ReceivedKA     = (  False,     False)
    Created        = (   True,      True)
    ReadyToAccept  = (   True,      True)
    DeletedByOther = (   True,      True)
    DeletedByUs    = (   True,      True)


LogClass = newClass('ControlEndpoint', Etypes)

