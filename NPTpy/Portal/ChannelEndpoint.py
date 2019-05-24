# Abstract class for channel endpoints

class ChannelEndpoint:

    def __init__(self, myID, myLink):
        self.myID   = myID
        self.myLink = myLink

    def sendMessage(self, data):
        header  = b''
        header += len(data).to_bytes(2, 'little') # 2B
        header += self.myID.to_bytes(2, 'little') # 2B
        self.myLink.sendPacket(header + data)     # 4B

    def acceptMessage(self, data):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
