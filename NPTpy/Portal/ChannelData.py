# A data channel
# Transfers data between an actual (local) connection
# and its channel within the portal-client link.

from ChannelEndpoint import ChannelEndpoint

class ChannelData(ChannelEndpoint):

    def __init__(self, myID, myLink, myCon):
        ChannelEndpoint.__init__(myID, myLink)
        self.myCon = myCon

    def acceptMessage(self, data):
        try:
            self.myCon.sendall(data)
        except ConnectionAbortedError:
            self.myLink.removeMe(self.myID)

    def close(self):
        self.myCon.tryClose()

    # Needed for select()
    def fileno(self):
        return self.con.fileno()

    # Called after select()
    def task(self):
        data = self.myCon.tryRecv(32768)
        if len(data) < 1:
            self.myLink.removeMe(self.myID)
            return
        self.sendMessage(data)
