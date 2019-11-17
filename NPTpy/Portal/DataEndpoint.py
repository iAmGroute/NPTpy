# A data channel
# Transfers data between an actual (local) connection
# and its channel within the portal-client link.

import Globals

from .Endpoint import Endpoint

class DataEndpoint(Endpoint):

    def __init__(self, myID, myIDF, parent, con):
        Endpoint.__init__(self, myID, myIDF, parent)
        self.con      = con
        self.readable = Globals.readables.new(self, isActive=True, canWake=True)
        self.writable = Globals.writables.new(self, isActive=True, canWake=False)

    def acceptMessage(self, data):
        try:
            self.con.socket.settimeout(None)
            self.con.sendall(data)
            self.con.socket.settimeout(0)
        except OSError:
            self.remove()

    # Needed for select()
    def fileno(self):
        return self.con.fileno()

    def getMessages(self):
        data = self.con.tryRecv(4088)
        if data is None:
            return b''
        if len(data) < 1:
            self.remove()
            return b''
        return self.formMessage(data)

