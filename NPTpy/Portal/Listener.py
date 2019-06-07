
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

        channelID = self.myLink.reserveChannel(self)
        if channelID > 0:
            self.allowSelect = False
            self.myLink.epControl.requestNewChannel(channelID, self.devicePort, self.deviceAddr)


    def accept(self, channelID, channelIDF):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()
        # connSocket.setblocking(False)

        self.myLink.upgradeChannel(channelID, channelIDF, connSocket)

        return True


    def decline(self, channelID, channelIDF):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()
        connSocket.setblocking(False)
        try:
            connSocket.close()
        except OSError:
            pass

        return True
