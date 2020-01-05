
from .Log import newClass

class Etypes:       # (Enabled, Displayed)
    Error           = (   True,      True)
    Initing         = (   True,      True)
    Inited          = (   True,      True)
    Closing         = (   True,      True)
    Closed          = (   True,      True)
    Shutdown        = (   True,      True)
    ShutdownDone    = (   True,      True)
    Connecting      = (   True,      True)
    Connected       = (   True,      True)
    Accepting       = (   True,      True)
    Accepted        = (   True,      True)
    Declining       = (   True,      True)
    Declined        = (   True,      True)
    Handshake       = (  False,     False)
    HandshakeResult = (   True,      True)
    Listen          = (   True,      True)
    Sending         = (  False,     False)
    SendingTo       = (  False,     False)
    Sent            = (  False,     False)
    Receiving       = (  False,     False)
    Received        = (  False,     False)
    ReceivedFrom    = (  False,     False)
    Content         = (  False,     False)


LogClass = newClass('Connector', Etypes)

