
import logging
import socket

from Common.Connector import Connector

from .ChannelEndpoint import ChannelEndpoint
from .ChannelControl  import ChannelControl
from .ChannelData     import ChannelData

log   = logging.getLogger(__name__ + '   ')
logEP = logging.getLogger(__name__ + ':EP')

class Link:

    class States:
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
        self.listeners    = []
        self.epControl    = ChannelControl(0, self)
        self.eps          = [epControl] # TODO: convert to slotList
        self.epls         = [None]      # The listeners that corespond to the above endpoints
        self.buffer       = b''
        self.state        = self.States.Disconnected
        self.conRT        = None


    def addListener(self, devicePort, deviceAddr, port, address):
        listener = Listener(len(self.listeners, self, devicePort, deviceAddr, port, address))
        self.listeners.append(listener)


    def close(self):
        self.conRT.tryClose()
        for ep in self.eps:
            ep.close()


    def removeEP(self, channelID):
        self.eps[channelID]  = None
        self.epls[channelID] = None
        self.epControl.requestDeleteChannel(channelID)


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


    # Called by ChannelEndpoint,
    # sends <packet> through the link to the remote portal.
    def sendPacket(self, packet):
        try:
            self.sendall(packet)
        except ConnectionAbortedError:
            log.exception(logEP)
            self.reconnect()


    # Functions called by control channel and listeners

    def reserveChannel(self, listener):
        channelID = len(self.eps)
        self.eps.append(None)
        self.epls.append(listener)
        return channelID


    def addChannel(self, channelID, conn):

        if channelID <= 0 or not conn:
            return False

        while channelID >= len(self.eps):
            self.eps.append(None)
            self.epls.append(None)

        if self.eps[channelID]:
            self.deleteChannel(channelID)

        self.eps[channelID] = ChannelData(channelID, self, conn)

        return True


    def newChannel(self, channelID, devicePort, deviceAddr):

        conn = Connector(logEP, Connector.new(socket.SOCK_STREAM, 2, self.parent.port, self.parent.address))
        for i in range(3):
            if conn.tryConnect((deviceAddr, devicePort)):
                break
            else:
                conn.tryClose()
        else:
            conn = None

        return self.addChannel(channelID, conn)


    def newChannelFromSocket(self, channelID, channelSocket):
        conn = Connector(logEP, channelSocket)
        return self.addChannel(channelID, conn)


    # Accept local connection
    # by calling accept() on the listener (= socket accept)
    # that corresponds to the channelID
    def acceptChannel(self, channelID):
        try:
            listener = self.epls[channelID]
            return listener.accept(channelID)
        except (IndexError, AttributeError):
            return False


    # Accept local connection
    # by calling decline() on the listener (= socket accept and close immediately)
    # that corresponds to the channelID
    def declineChannel(self, channelID):
        try:
            listener = self.epls[channelID]
            return listener.accept(channelID)
        except (IndexError, AttributeError):
            return False


    def deleteChannel(self, channelID):
        try:
            self.eps[channelID].close()
            self.eps[channelID]  = None
            self.epls[channelID] = None
            return True
        except (IndexError, AttributeError):
            return False

