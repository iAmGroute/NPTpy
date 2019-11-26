
from enum import Enum, auto

class Etypes(Enum):
    Inited         = auto()
    Deleted        = auto()
    Corrupted      = auto()
    SendingKA      = auto()
    ReceivedKA     = auto()
    Created        = auto()
    ReadyToAccept  = auto()
    DeletedByOther = auto()
    DeletedByUs    = auto()

class LogClass:
    name     = 'ControlEndpoint'
    etypes   = Etypes
    disabled = [
    ]

