
import socket

import Globals

from Common.SlotMap        import SlotMap
from Common.Connector      import Connector
from Common.AsyncConnector import AsyncConnector
from NextLoop              import loop
from .Endpoint             import Endpoint
from .ControlEndpoint      import ControlEndpoint
from .DataEndpoint         import DataEndpoint

class Channels:

    def __init__(self, myLink, ltPort, ltAddr):
        self.myLink    = myLink
        self.ltPort    = ltPort
        self.ltAddr    = ltAddr
        self.epControl = ControlEndpoint(0, 0, self, Globals.timeoutReminder)
        self.eps       = SlotMap([self.epControl])
        assert self.eps[0] is self.epControl

    def teardown(self):
        self.epControl = None
        self.eps       = None

    def reset(self):
        self.epControl.reset()
        for i in self.eps.listIDs()[1:]:
            del self.eps[i]

    def isEmpty(self):
        return len(self.eps) <= 1

# Data flow

    def readAll(self, readables):
        result = b''
        for ep in self.eps:
            if ep in readables:
                result += ep.getMessages()
        return result

    def acceptMessage(self, channelID, data):
        ep = self.eps[channelID]
        if ep:
            ep.acceptMessage(data)

    def send(self, data, untracked=False):
        self.myLink.send(data, untracked)

    def sendKA(self):
        self.epControl.sendKA()

# Channel management

    def _remove(self, channelID):
        ep = self.eps[channelID]
        if ep:
            del self.eps[channelID]
            loop.run(self.epControl.requestDeleteChannel(channelID, ep.myIDF))

    def _finish(self, channelID):
        ep = self.eps[channelID]
        if ep:
            loop.run(self.epControl.requestCloseChannel(channelID, ep.myIDF))

    def reserveChannel(self):
        cID = self.eps.append(0)
        ep  = Endpoint(cID, -1, self)
        self.eps[cID] = ep
        return cID

    def addChannel(self, channelIDF, connSocket):
        conn = Connector(fromSocket=connSocket)
        cID  = self.eps.append(0)
        ep   = DataEndpoint(conn, new=(cID, channelIDF, self))
        self.eps[cID] = ep
        return cID

    async def requestChannel(self, remotePort, remoteAddr):
        channelID = self.reserveChannel()
        if channelID > 0:
            result = await self.epControl.requestNewChannel(channelID, remotePort, remoteAddr)
            if not result:
                self.deleteChannel(channelID)
            return result
        else:
            return None

    def upgradeChannel(self, channelID, channelIDF, connSocket):
        conn  = Connector(fromSocket=connSocket)
        ep    = self.eps[channelID]
        newEP = DataEndpoint(conn, fromEndpoint=ep)
        newEP.myIDF = channelIDF
        self.eps[channelID] = newEP
        return True

    async def newChannel(self, channelIDF, devicePort, deviceAddr):
        for _ in range(3):
            conn = AsyncConnector(
                Globals.readables,
                Globals.writables,
                new=(socket.SOCK_STREAM, 5, self.ltPort, self.ltAddr),
            )
            if await conn.tryConnectAsync((deviceAddr, devicePort)):
                conn.socket.settimeout(0)
                return self.addChannel(channelIDF, conn.socket)
        return 0

    def deleteChannel(self, channelID):
        if channelID > 0:
            try:
                del self.eps[channelID]
                return True
            except (IndexError, AttributeError):
                return False
        else:
            return False

    def closeChannel(self, channelID):
        if channelID > 0:
            try:
                ep = self.eps[channelID]
                ep.close()
                if ep.finished:
                    # is also closed in the reverse direction
                    del self.eps[channelID]
                return True
            except (IndexError, AttributeError):
                return False
        else:
            return False

