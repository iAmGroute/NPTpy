
from enum import Enum

class Etypes(Enum):
    Inited  = 0
    Deleted = 1

class LogClass:
    typeID = None
    name   = 'Listener'
    etypes = Etypes

