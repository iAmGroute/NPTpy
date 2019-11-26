
from enum import Enum, auto

class Etypes(Enum):
    Inited        = auto()
    Deleted       = auto()
    Connect       = auto()
    ConnectResult = auto()
    Disconnect    = auto()

class LogClass:
    name   = 'Portal'
    etypes = Etypes

