
from LogPack import newClass

class Etypes:        # (Enabled, Displayed)
    Inited           = (   True,      True)
    Deleted          = (   True,      True)
    Connect          = (   True,      True)
    ConnectHandshake = (   True,      True)
    ConnectAuth      = (   True,      True)
    ConnectResult    = (   True,      True)
    Disconnect       = (   True,      True)
    ReplyNotOK       = (   True,      True)


LogClass = newClass('Portal', Etypes)

