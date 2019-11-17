
from enum import Enum, auto

class Etypes(Enum):
    Error           = auto()
    Initing         = auto()
    Inited          = auto()
    Closing         = auto()
    Closed          = auto()
    Connecting      = auto()
    Connected       = auto()
    Accepting       = auto()
    Accepted        = auto()
    Declining       = auto()
    Declined        = auto()
    Handshake       = auto()
    HandshakeResult = auto()
    Listen          = auto()
    Sending         = auto()
    SendingTo       = auto()
    Sent            = auto()
    Receiving       = auto()
    Received        = auto()
    ReceivedFrom    = auto()
    Content         = auto()

class LogClass:
    name     = 'Connector'
    etypes   = Etypes
    disabled = [
        Etypes.Content,
        Etypes.Handshake
    ]

