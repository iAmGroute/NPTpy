
from enum import Enum, auto

class Etypes(Enum):
    Inited     = auto()
    Deleting   = auto()
    Reset      = auto()
    Attach     = auto()
    Detach     = auto()
    Fire       = auto()
    FireResult = auto()

class LogClass:
    name     = 'Promise'
    etypes   = Etypes
    disabletd = [
    ]

