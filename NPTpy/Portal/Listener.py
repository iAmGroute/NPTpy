
import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Listener:

    def __init__(self, myID, myLink, devicePort, deviceAddr, myPort, myAddress):
        self.myID       = myID
        self.myLink     = myLink
        self.devicePort = devicePort
        self.deviceAddr = deviceAddr
        self.con        = Connector(log, Connector.new(socket.SOCK_STREAM, None, myPort, myAddress))
        self.con.listen()
        self.allowSelect = True


    def close(self):
        self.con.tryClose()


    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    # Called after select()
    def task(self):
        self.allowSelect = False
        channelID = self.myLink.reserveChannel(self)
        self.myLink.epControl.requestNewChannel(channelID, self.devicePort, self.deviceAddr)


    def accept(self, channelID):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()
        # connSocket.setblocking(False)

        self.myLink.newChannelFromSocket(channelID, connSocket)

        return True


    def decline(self, channelID):

        if self.allowSelect:
            return False

        self.allowSelect = True

        connSocket, addr = self.con.accept()
        connSocket.setblocking(False)
        try:
            self.socket.close()
        except socket.error:
            pass

        return True
