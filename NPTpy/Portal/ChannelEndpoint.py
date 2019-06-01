# Abstract class for channel endpoints

class ChannelEndpoint:

    def __init__(self, myID, myIDF, myLink, myListener=None):
        self.myID       = myID       # Local ID
        self.myIDF      = myIDF      # Foreign ID
        self.myLink     = myLink
        self.myListener = myListener

    def sendMessage(self, data):
        header  = b''
        header += len(data).to_bytes(2, 'little')  # 2B
        header += self.myIDF.to_bytes(2, 'little') # 2B
        self.myLink.sendPacket(header + data)      # 4B

    def acceptMessage(self, data):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class ChannelPlaceholder(ChannelEndpoint):

    def acceptMessage(self, data):
        pass

    def close(self):
        pass
