
from enum import Enum, auto

class Etypes(Enum):
    Inited  = auto()
    Deleted = auto()

class LogClass:
    name   = 'Listener'
    etypes = Etypes

