# Abstract class for channel endpoints

class ChannelEndpoint:

    def __init__(self, myID, myLink)
        self.myID   = myID
        self.myLink = myLink

    def sendMessage(self, data):
        header = b'0000'
        header[0:2] = len(data).to_bytes(2, 'little')
        header[2:4] = self.myID.to_bytes(2, 'little')
        self.myLink.sendPacket(header + data)

    def acceptMessage(self, data):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
