# Base class for channel endpoints

import Globals
import ConfigFields as CF

from .Endpoint_log import LogClass, Etypes

class Endpoint:

    fields = [
        # Name,   Type,     Readable, Writable
        # ('myID',  CF.Int(),  True,    False),
        ('myIDF', CF.Int(),  True,    True)
    ]

    def __init__(self, myID, myIDF, parent):
        self.log    = Globals.logger.new(LogClass)
        self.myID   = myID   # Local ID
        self.myIDF  = myIDF  # Foreign ID
        self.parent = parent
        self.log(Etypes.Inited, myID, myIDF)

    def remove(self):
        self.parent._remove(self.myID)

    def formMessage(self, data):
        header  = b''
        header += len(data).to_bytes(2, 'little')
        header += self.myIDF.to_bytes(2, 'little')
        return header + data

    def getMessages(self):
        # pylint: disable=no-self-use
        return b''

    def acceptMessage(self, data):
        pass

