
from enum import Enum, auto

class Etypes(Enum):
    Inited         = auto()
    Deleted        = auto()
    Corrupted      = auto()
    ReceivedKA     = auto()
    ReadyToAccept  = auto()
    DeletedByOther = auto()
    DeletedByUs    = auto()

class LogClass:
    name     = 'ControlEndpoint'
    etypes   = Etypes
    disabled = {}

