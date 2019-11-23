
from enum import Enum, auto

class Etypes(Enum):
    Inited        = auto()
    Deleted       = auto()
    NewConnection = auto()
    Accept        = auto()
    Decline       = auto()

class LogClass:
    name   = 'Listener'
    etypes = Etypes

