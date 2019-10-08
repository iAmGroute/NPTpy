
from enum import Enum

class Etypes(Enum):
    Error           = 0
    Inited          = 1
    Deleted         = 2
    Closing         = 3
    Closed          = 4
    CloseError      = 5
    Connecting      = 6
    Connected       = 7
    Accepting       = 8
    Accepted        = 9
    Declining       = 10
    Declined        = 11
    Handshake       = 12
    HandshakeResult = 13
    Listen          = 14
    Sending         = 15
    SendingTo       = 16
    Sent            = 17
    Receiving       = 18
    Received        = 19
    ReceivedFrom    = 20
    Content         = 21

class LogClass:
    typeID = None
    name   = 'Connector'
    etypes = Etypes

