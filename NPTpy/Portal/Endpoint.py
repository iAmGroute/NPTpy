# Base class for channel endpoints

import ConfigFields as CF

from LogPack    import logger

from .Endpoint_log import LogClass, Etypes

class Endpoint:

    fields = [
        # Name,   Type,     Readable, Writable
        # ('myID',  CF.Int(),  True,    False),
        ('myIDF', CF.Int(),  True,    True)
    ]

    def __init__(self, myID, myIDF, parent):
        self.log    = logger.new(LogClass)
        self.myID   = myID   # Local ID
        self.myIDF  = myIDF  # Foreign ID
        self.parent = parent
        self.log(Etypes.Inited, myID, myIDF)

    def remove(self):
        # pylint: disable=protected-access
        self.parent._remove(self.myID)

    def finish(self):
        # pylint: disable=protected-access
        self.parent._finish(self.myID)

    def formMessage(self, data):
        header  = b''
        header += len(data).to_bytes(2, 'little')
        header += self.myIDF.to_bytes(2, 'little')
        return header + data

    def close(self):
        pass

    def getMessages(self):
        # pylint: disable=no-self-use
        return b''

    def acceptMessage(self, data):
        pass

