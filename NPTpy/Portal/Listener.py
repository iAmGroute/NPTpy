
import logging
import socket

import Globals
import ConfigFields as CF

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Listener:

    fields = [
        # Name,         Type,         Readable, Writable
        # ('myID',        CF.Int(),     True,     False),
        ('remotePort',  CF.Port(),    True,     True),
        ('remoteAddr',  CF.Address(), True,     True),
        ('localPort',   CF.Port(),    True,     True),
        ('localAddr',   CF.Address(), True,     True),
        ('waiting',     CF.Bool(),    True,     True),
        ('reserveID',   CF.Int(),     True,     True)
    ]

    def __init__(self, myID, myLink, remotePort, remoteAddr, localPort, localAddr):
        self.myID        = myID
        self.myLink      = myLink
        self.remotePort  = remotePort
        self.remoteAddr  = remoteAddr
        self.localPort   = localPort
        self.localAddr   = localAddr
        self.readable    = Globals.readables.new(self, isActive=True, canWake=True)
        self.waiting     = False
        self.reserveID   = -1
        self.con         = Connector(log, Connector.new(socket.SOCK_STREAM, 0, localPort, localAddr))
        self.con.listen()
        self.reminder    = Globals.resetReminder.getDelegate(onRun={ self.handleRemind })


    def handleRemind(self):
        if self.waiting:
            self.decline()
        return False


    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    def rtask(self, readables, writables):
        self.reminder.skipNext = True
        self.readable.off()
        self.waiting = True
        self.myLink.connectAndCall(self.handleConnected)


    def handleConnected(self, ok):
        if ok:
            self.reserveID = self.myLink.reserveChannel(self)
            if self.reserveID > 0:
                self.myLink.epControl.requestNewChannel(self.reserveID, self.remotePort, self.remoteAddr)
            else:
                self.decline()
        else:
            self.decline()


    def accept(self, channelID, channelIDF):

        self.readable.on()
        self.waiting = False

        connSocket, addr = self.con.tryAccept()
        if not connSocket:
            self.myLink.deleteChannel(self.reserveID)
            self.reserveID = -1
            return False
        connSocket.settimeout(0)

        self.myLink.upgradeChannel(channelID, channelIDF, connSocket)
        self.reserveID = -1

        return True


    def decline(self):

        self.readable.on()
        self.waiting = False

        addr = self.con.tryDecline()

        self.myLink.deleteChannel(self.reserveID)
        self.reserveID = -1

        return bool(addr)

