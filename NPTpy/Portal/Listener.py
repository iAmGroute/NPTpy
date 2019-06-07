
import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Listener:

    def __init__(self, myID, myLink, devicePort, deviceAddr, myPort, myAddress):
        self.myID        = myID
        self.myLink      = myLink
        self.devicePort  = devicePort
        self.deviceAddr  = deviceAddr
        self.allowSelect = True
        self.reserveID   = -1
        self.con         = Connector(log, Connector.new(socket.SOCK_STREAM, None, myPort, myAddress))
        self.con.listen()


    def close(self):
        self.con.tryClose()


    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    # Called after select()
    def task(self):

        if not self.myLink.isConnected():
            return

        self.reserveID = self.myLink.reserveChannel(self)
        if self.reserveID > 0:
            self.allowSelect = False
            self.myLink.epControl.requestNewChannel(self.reserveID, self.devicePort, self.deviceAddr)


    def accept(self, channelID, channelIDF):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()
        # connSocket.setblocking(False)

        self.myLink.upgradeChannel(channelID, channelIDF, connSocket)

        return True


    def decline(self):

        if self.allowSelect:
            return False

        self.allowSelect = True

        self.myLink.deleteChannel(self.reserveID)

        connSocket, addr = self.con.accept()
        connSocket.setblocking(False)
        try:
            connSocket.close()
        except OSError:
            pass

        return True
