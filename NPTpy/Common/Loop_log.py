
from enum import Enum, auto

class Etypes(Enum):
    Stopping   = auto()
    Stopped    = auto()
    Watching   = auto()
    Resolving  = auto()
    Continuing = auto()
    NotFound   = auto()
    Running    = auto()
    RunError   = auto()
    Finished   = auto()
    Paused     = auto()

class LogClass:
    name     = 'Loop'
    etypes   = Etypes
    disabled = [
    ]

