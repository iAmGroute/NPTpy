
import logging
import socket

from Common.Connector import Connector

from .ChannelEndpoint import ChannelEndpoint
from .ChannelControl  import ChannelControl
from .ChannelData     import ChannelData

log   = logging.getLogger(__name__ + '   ')
logEP = logging.getLogger(__name__ + ':EP')

class Link:

    class States(Enum):
        Disconnected = 0
        WaitReady    = 1
        Forwarding   = 2

    def __init__(self, myID, myPortal, myToken, relayPort, relayAddr, myPort=0, myAddress='0.0.0.0'):
        self.myID         = myID
        self.myPortal     = myPortal
        self.myToken      = myToken
        self.relayPort    = relayPort
        self.relayAddress = relayAddress
        self.myPort       = myPort
        self.myAddress    = myAddress
        self.eps          = [ChannelControl(0, self)] # TODO: convert to slotList
        self.buffer       = b''
        self.state        = self.States.Disconnected
        self.conRT        = None

    def sendPacket(self, packet):
        try:
            self.sendall(packet)
        except ConnectionAbortedError:
            log.exception(logEP)
            self.reconnect()

    def close(self):
        self.conRT.tryClose()
        for ep in self.eps:
            ep.close()

    def removeEP(self, channelID):
        self.eps[channelID] = None
        self.eps[0].requestDeleteChannel(channelID)

    def maintenace(self):
        if not self.conRT:
            self.taskConnect()

    def reconnect(self):
        self.conRT.tryClose()
        self.conRT = None
        self.state = self.States.Disconnected
        self.taskConnect()

    def disconnect(self):
        self.close()
        self.myPortal.removeLink(self.myID)

    # Needed for select()
    def fileno(self):
        return self.conRT.fileno()

    # Called after select()
    def task(self):
        if   self.state == self.States.Disconnected: self.taskConnect() # should not ever be called
        elif self.state == self.States.WaitReady:    self.taskReady()
        elif self.state == self.States.Forwarding:   self.taskForward()

    # TODO: add listeners (server sockets) for new channel requests

    def taskConnect(self):

        assert not self.conRT

        conRT = Connector(log, Connector.new(socket.SOCK_STREAM, 2, self.myPort, self.myAddress))
        data = self.myToken + b'0' * 56
        for i in range(3):
            if conRT.tryConnect((self.relayAddr, self.relayPort), data):
                conRT.setKeepAlive()
                break
            else:
                conRT.tryClose()
        else:
            conRT = None

        if conRT:
            self.conRT = conRT
            self.state = self.States.WaitReady

    def taskReady(self):
        data = self.conRT.tryRecv(8)
        if   data == b'Ready !\n': self.state = self.States.Forwarding
        elif data == b'Bad T !\n': self.disconnect()
        else:                      self.reconnect()

    def taskForward(self):

        data = self.tryRecv(32768)
        if len(data) < 1:
            self.reconnect()
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


    # Functions called by control channel

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
