
import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Listener:

    def __init__(self, myID, myLink, devicePort, deviceAddr, myPort, myAddress):
        self.myID          = myID
        self.myLink        = myLink
        self.devicePort    = devicePort
        self.deviceAddress = deviceAddress
        self.con           = Connector(log, Connector.new(socket.SOCK_STREAM, None, myPort, myAddress))
        self.con.setblocking(False)
        self.con.listen()
        self.pending = 0


    def close(self):
        self.con.tryClose()


    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    # Called after select()
    def task(self):
        self.pending += 1
        channelID = reserveChannel(self)
        self.myLink.epControl.requestNewChannel(channelID, self.devicePort, self.deviceAddr)


    def accept(self, channelID):

        if self.pending <= 0:
            return False

        self.pending -= 1

        connSocket, addr = self.con.accept()
        connSocket.setblocking(False)

        self.myLink.newChannelFromSocket(channelID, connSocket)

        return True


    def decline(self, channelID):

        if self.pending <= 0:
            return False

        self.pending -= 1

        connSocket, addr = self.con.accept()
        connSocket.setblocking(False)
        try:
            self.socket.close()
        except socket.error:
            pass

        return True
