# A data channel
# Transfers data between an actual (local) connection
# and its channel within the portal-client link.

import Globals

from .Endpoint     import Endpoint
# TODO: create DataEndpoint log
from .Endpoint_log import LogClass

class DataEndpoint(Endpoint):

    def __init__(self, con, new=None, fromEndpoint=None):
        if new:
            Endpoint.__init__(self, *new)
        elif fromEndpoint:
            self.log      = fromEndpoint.log
            self.myID     = fromEndpoint.myID
            self.myIDF    = fromEndpoint.myIDF
            self.parent   = fromEndpoint.parent
            self.finished = fromEndpoint.finished
        self.log.upgrade(LogClass)
        self.con      = con
        self.readable = Globals.readables.new(self, True)

    def close(self):
        self.con.tryShutdown(read=False, write=True)

    def acceptMessage(self, data):
        try:
            self.con.socket.settimeout(1)
            self.con.sendall(data)
            self.con.socket.settimeout(0)
        except OSError:
            self.remove()

    # Needed for select()
    def fileno(self):
        return self.con.fileno()

    def getMessages(self):
        if self.finished:
            return b''
        data = self.con.tryRecv(4088)
        if data is None:
            return b''
        if not data:
            self.readable.off()
            self.finish()
            return b''
        return self.formMessage(data)

