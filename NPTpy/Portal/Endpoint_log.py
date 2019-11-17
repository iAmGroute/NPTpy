
from enum import Enum, auto

class Etypes(Enum):
    Inited  = auto()
    Deleted = auto()

class LogClass:
    name   = 'Endpoint'
    etypes = Etypes

