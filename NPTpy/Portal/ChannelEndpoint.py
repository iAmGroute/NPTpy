# Abstract class for channel endpoints

from enum import Enum

import Globals
import ConfigFields as CF

class Etypes(Enum):
    Inited  = 0
    Deleted = 1

class ChannelEndpoint:

    fields = [
        # Name,         Type,      Readable, Writable
        # ('myID',        CF.Int(),  True,     False),
        ('myIDF',       CF.Int(),  True,     True)
    ]

    def __init__(self, myID, myIDF, myLink):
        self.myID   = myID   # Local ID
        self.myIDF  = myIDF  # Foreign ID
        self.myLink = myLink
        self.log    = Globals.logger.new(Globals.LogTypes.ChannelEndpoint)
        self.log(Etypes.Inited, (myID, myIDF))

    def __del__(self):
        self.log(Etypes.Deleted, ())

    def sendMessage(self, data, untracked=False):
        header  = b''
        header += len(data).to_bytes(2, 'little')        # 2B
        header += self.myIDF.to_bytes(2, 'little')       # 2B
        self.myLink.sendPacket(header + data, untracked) # 4B

    def acceptMessage(self, data):
        raise NotImplementedError()


class ChannelPlaceholder(ChannelEndpoint):

    myListener = None

    def acceptMessage(self, data):
        pass

