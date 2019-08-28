
import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Listener:

    def __init__(self, myID, myLink, remotePort, remoteAddr, localPort, localAddr):
        self.myID        = myID
        self.myLink      = myLink
        self.remotePort  = remotePort
        self.remoteAddr  = remoteAddr
        self.localPort   = localPort
        self.localAddr   = localAddr
        self.allowSelect = True
        self.reserveID   = -1
        self.con         = Connector(log, Connector.new(socket.SOCK_STREAM, None, localPort, localAddr))
        self.con.listen()


    def close(self):
        self.con.tryClose()


    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    # Called after select()
    def task(self):

        if not self.myLink.isConnected():
            self.con.decline()
            return

        self.reserveID = self.myLink.reserveChannel(self)
        if self.reserveID > 0:
            self.allowSelect = False
            self.myLink.epControl.requestNewChannel(self.reserveID, self.remotePort, self.remoteAddr)


    def accept(self, channelID, channelIDF):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()

        self.myLink.upgradeChannel(channelID, channelIDF, connSocket)

        return True


    def decline(self):

        if self.allowSelect:
            return False

        self.allowSelect = True

        self.myLink.deleteChannel(self.reserveID)

        self.con.decline()

        return True
