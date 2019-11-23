
import logging
import socket

import Globals
import ConfigFields as CF

from Common.Connector import Connector
from Common.Async     import loop

from .Listener_log import LogClass, Etypes

log = logging.getLogger(__name__)

class Listener:

    fields = [
        # Name,         Type,         Readable, Writable
        # ('myID',        CF.Int(),     True,     False),
        ('remotePort',  CF.Port(),    True,     True),
        ('remoteAddr',  CF.Address(), True,     True),
        ('localPort',   CF.Port(),    True,     True),
        ('localAddr',   CF.Address(), True,     True)
    ]

    def __init__(self, myID, myLink, remotePort, remoteAddr, localPort, localAddr):
        self.log         = Globals.logger.new(LogClass)
        self.myID        = myID
        self.myLink      = myLink
        self.remotePort  = remotePort
        self.remoteAddr  = remoteAddr
        self.localPort   = localPort
        self.localAddr   = localAddr
        self.con         = Connector(new=(socket.SOCK_STREAM, 0, localPort, localAddr))
        self.con.listen()
        self.readable    = Globals.readables.new(self, isActive=True, canWake=True)
        self.log(Etypes.Inited, myID, remotePort, remoteAddr, localPort, localAddr)

    # Needed for select()
    def fileno(self):
        return self.con.fileno()

    def rtask(self):
        self.log(Etypes.NewConnection)
        self.readable.off()
        loop.run(self.main())

    async def main(self):
        result = await self.myLink.requestChannel(self.remotePort, self.remoteAddr)
        self.readable.on()
        if result:
            self.accept(*result)
        else:
            self.decline()

    def accept(self, channelID, channelIDF):
        self.log(Etypes.Accept, channelID, channelIDF)
        connSocket, addr = self.con.tryAccept()
        if connSocket:
            connSocket.settimeout(0)
            self.myLink.upgradeChannel(channelID, channelIDF, connSocket)
        else:
            self.myLink.deleteChannel(channelID)

    def decline(self):
        self.log(Etypes.Decline)
        addr = self.con.tryDecline()

