
import logging
import socket

from Common.Connector import Connector

from .ChannelEndpoint import ChannelEndpoint
from .ChannelControl  import ChannelControl
from .ChannelData     import ChannelData

log   = logging.getLogger(__name__ + '   ')
logEP = logging.getLogger(__name__ + ':EP')

class Link:

    def __init__(self, myID, myPortal, mySocket):
        self.myID     = myID
        self.myPortal = myPortal
        self.con      = Connector(log, mySocket)
        self.eps      = [ChannelControl(0, self)] # TODO: convert to slotList
        self.buffer   = b''

    def connectionDropped(self):
        # TODO:
        # try to re-establish the connection,
        # without losing the active channels
        # if all else fails:
        self.close()
        self.myPortal.removeLink(self.myID)

    def sendPacket(self, packet):
        try:
            self.sendall(packet)
        except ConnectionAbortedError:
            log.exception(logEP)
            self.connectionDropped()

    def close(self):
        self.con.tryClose()
        for ep in self.eps:
            ep.close()

    def removeEP(self, channelID):
        self.eps[channelID] = None
        self.eps[0].requestDeleteChannel(channelID)

    # Needed for select()
    def fileno(self):
        return self.con.fileno()


    # TODO: add 2-state implementation (bring from RelayConn)
    # since the relay will start the connection with a 'Ready !' message

    # TODO: add listeners (server sockets) for new channel requests


    # Called after select()
    def task(self):

        data = self.tryRecv(32768)
        if len(data) < 1:
            self.connectionDropped()
            return

        self.buffer += data

        while len(self.buffer) >= 4:

            header = self.buffer[0:4]
            totalLen = int.from_bytes(header[0:2], 'little')
            epID     = int.from_bytes(header[2:4], 'little')

            # Check if we need more bytes to complete the packet
            if totalLen > len(self.buffer):
                break

            ep = self.eps[epID] if epID < len(self.eps) else None
            if ep:
                ep.acceptMessage(self.buffer[4:totalLen])
            else:
                log.warn('    epID not found')

            self.buffer = self.buffer[totalLen:]


    # Control channel functions

    def newChannel(channelID, devicePort, deviceAddr):

        conn = Connector(logEP, Connector.new(socket.SOCK_STREAM, 2, self.parent.port, self.parent.address))
        for i in range(3):
            if conn.tryConnect((deviceAddr, devicePort)):
                break
            else:
                conn.tryClose()
        else:
            conn = None

        if conn:

            while channelID >= len(self.eps):
                self.eps.append(None)

            if self.eps[channelID]:
                self.deleteChannel(channelID)

            self.eps[channelID] = ChannelData(channelID, self, conn)

            return True

        else:
            return False

    def acceptChannel(channelID):
        # TODO: accept incoming connection
        # by calling accept() on the listener (= socket accept)
        # that corresponds to the channelID
        return False

    def declineChannel(channelID):
        # TODO: accept incoming connection
        # by calling decline() on the listener (= socket accept and close immediately)
        # that corresponds to the channelID
        return False

    def deleteChannel(channelID):

        if channelID >= len(self.eps):
            return False

        ep = self.eps[channelID]
        if ep:
            ep.close()
            self.eps[channelID] = None
            return True
        else:
            return False
