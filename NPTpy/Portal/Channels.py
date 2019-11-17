
import socket

import Globals

from Common.SlotList       import SlotList
from Common.Connector      import Connector
from Common.AsyncConnector import AsyncConnector
from Common.Async          import loop
from .Endpoint             import Endpoint
from .ControlEndpoint      import ControlEndpoint
from .DataEndpoint         import DataEndpoint

class Channels:

    def __init__(self, myLink, ltPort, ltAddr):
        self.myLink    = myLink
        self.ltPort    = ltPort
        self.ltAddr    = ltAddr
        self.epControl = ControlEndpoint(0, 0, self)
        self.eps       = SlotList([self.epControl])
        assert self.eps[0] is self.epControl

    def teardown(self):
        self.epControl = None
        self.eps       = None

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

    def send(self, data):
        self.myLink.send(data)

# Channel management

    def _remove(self, channelID):
        ep = self.eps[channelID]
        if ep:
            del self.eps[channelID]
            loop.run(self.epControl.requestDeleteChannel(channelID, ep.myIDF))

    def reserveChannel(self):
        cID = self.eps.append(0)
        ep  = Endpoint(cID, -1, self)
        self.eps[cID] = ep
        return cID

    def addChannel(self, channelIDF, connSocket):
        conn = Connector(connSocket)
        cID  = self.eps.append(0)
        ep   = DataEndpoint(cID, channelIDF, self, conn)
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
        conn = Connector(connSocket)
        ep   = self.eps[channelID]
        self.eps[channelID] = DataEndpoint(channelID, channelIDF, self, conn)
        return True

    async def newChannel(self, channelIDF, devicePort, deviceAddr):
        for i in range(3):
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
