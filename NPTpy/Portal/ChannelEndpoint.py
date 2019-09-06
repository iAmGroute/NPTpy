# Abstract class for channel endpoints

import ConfigFields as CF

class ChannelEndpoint:

    fields = [
        # Name,         Type,      Writable
        # ('myID',        CF.Int(),  False),
        ('myIDF',       CF.Int(),  True),
        ('allowSelect', CF.Bool(), True)
    ]

    def __init__(self, myID, myIDF, myLink):
        self.myID   = myID       # Local ID
        self.myIDF  = myIDF      # Foreign ID
        self.myLink = myLink
        self.allowSelect = False # Temporary

    def sendMessage(self, data):
        header  = b''
        header += len(data).to_bytes(2, 'little')  # 2B
        header += self.myIDF.to_bytes(2, 'little') # 2B
        self.myLink.sendPacket(header + data)      # 4B

    def acceptMessage(self, data):
        raise NotImplementedError()


class ChannelPlaceholder(ChannelEndpoint):

    myListener = None

    def acceptMessage(self, data):
        pass

