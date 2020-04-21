
from LogPack import newClass

class Etypes:     # (Enabled, Displayed)
    Inited        = (   True,      True)
    Deleted       = (   True,      True)
    Connect       = (   True,      True)
    ConnectResult = (   True,      True)
    Disconnect    = (   True,      True)


LogClass = newClass('Link', Etypes)

