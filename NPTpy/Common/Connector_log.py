
from enum import Enum

class Etypes(Enum):
    Error           = 0
    Initing         = 1
    Inited          = 2
    Deleting        = 3
    Deleted         = 4
    Closing         = 5
    Closed          = 6
    Connecting      = 7
    Connected       = 8
    Accepting       = 9
    Accepted        = 10
    Declining       = 11
    Declined        = 12
    Handshake       = 13
    HandshakeResult = 14
    Listen          = 15
    Sending         = 16
    SendingTo       = 17
    Sent            = 18
    Receiving       = 19
    Received        = 20
    ReceivedFrom    = 21
    Content         = 22

class LogClass:
    typeID = None
    name   = 'Connector'
    etypes = Etypes

