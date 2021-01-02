
from LogPack import newClass

class Etypes:      # (Enabled, Displayed)
    Inited         = (   True,      True)
    Deleted        = (   True,      True)
    Connect        = (   True,      True)
    ConnectResult  = (   True,      True)
    ConnectionLost = (   True,      True)
    Disconnect     = (   True,      True)
    Reconnect      = (   True,      True)
    Error          = (   True,      True)


LogClass = newClass('Link', Etypes)

