# A data channel
# Transfers data between an actual (local) connection
# and its channel within the portal-client link.

import Globals

from .ChannelEndpoint import ChannelEndpoint

class ChannelData(ChannelEndpoint):

    def __init__(self, myID, myIDF, myLink, myCon):
        ChannelEndpoint.__init__(self, myID, myIDF, myLink)
        self.myCon = myCon
        self.readable = Globals.readables.new(self, isActive=True, canWake=False)
        self.writable = Globals.writables.new(self, isActive=True, canWake=False)

    def acceptMessage(self, data):
        try:
            self.myCon.sendall(data)
        except OSError:
            self.myLink.removeEP(self.myID)

    # Needed for select()
    def fileno(self):
        return self.myCon.fileno()

    def rtask(self):
        data = self.myCon.tryRecv(32768)
        if data is None:
            return
        if len(data) < 1:
            self.myLink.removeEP(self.myID)
            return
        self.sendMessage(data)

