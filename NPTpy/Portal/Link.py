
import logging
import socket

from Common.SmartTabs import t
from Common.SlotList  import SlotList

from Common.Connector import Connector

from .ChannelEndpoint import ChannelEndpoint, ChannelPlaceholder
from .ChannelControl  import ChannelControl
from .ChannelData     import ChannelData
from .Listener        import Listener

log   = logging.getLogger(__name__ + '    ')
logEP = logging.getLogger(__name__ + ' :EP')

class Link:

    class States:
        Disconnected = 0
        WaitReady    = 1
        Forwarding   = 2


    def __init__(self, isClient, myID, myPortal, otherPortalID, rtPort=0, rtAddr='0.0.0.0', ltPort=0, ltAddr='0.0.0.0'):

        self.isClient      = isClient
        self.myID          = myID
        self.myPortal      = myPortal
        self.otherPortalID = otherPortalID
        self.rtPort        = rtPort
        self.rtAddr        = rtAddr
        self.ltPort        = ltPort
        self.ltAddr        = ltAddr

        self.listeners     = SlotList(6)

        self.epControl     = ChannelControl(0, 0, self)
        self.eps           = SlotList(10, [self.epControl])
        assert self.eps[0] is self.epControl

        self.buffer        = b''
        self.state         = self.States.Disconnected
        self.conRT         = None
        self.allowSelect   = False


    def close(self):
        self.conRT.tryClose()
        self.conRT       = None
        self.allowSelect = False
        for ep in self.eps:
            ep.close()
            del self.eps[ep.myID]
        for listener in self.listeners:
            listener.close()
            del self.listeners[listener.myID]


    def addListener(self, devicePort, deviceAddr, port, address):
        listener      = Listener(-1, self, devicePort, deviceAddr, port, address)
        listenerID    = self.listeners.append(listener)
        listener.myID = listenerID
        return listener


    def removeEP(self, channelID):
        ep = self.eps[channelID]
        if ep:
            del self.eps[channelID]
            log.info(t('Channel\t [{0:5d}] closed locally'.format(channelID)))
            self.epControl.requestDeleteChannel(channelID, ep.myIDF)


    def secureForward(self):
        try:
            if self.isClient:
                self.conRT.secureClient(serverHostname='portal', caFilename='portal.cer')
            else:
                self.conRT.secureServer(certFilename='portal.cer', keyFilename='portal.key')
            self.conRT.socket.settimeout(0)
            self.state = self.States.Forwarding
        except OSError as e:
            log.error(e)
            self.reconnect()


    def disconnect(self):
        self.conRT.tryClose()
        self.conRT       = None
        self.allowSelect = False
        for ep in self.eps:
            ep.allowSelect = False
        for listener in self.listeners:
            if not listener.allowSelect:
                listener.decline()
            listener.allowSelect = True
        self.state = self.States.Disconnected


    def reconnect(self):
        self.disconnect()
        self.requestConnect()


    def requestConnect(self):
        if self.isClient:
            self.myPortal.connectToPortal(self.otherPortalID)


    def isConnected(self):
        if self.state == self.States.Disconnected:
            self.requestConnect()
        return self.state == self.States.Forwarding


    def connectToRelay(self, token, relayPort, relayAddr):

        if self.conRT:
            self.disconnect()

        data = token + b'0' * 56

        for i in range(3):
            conRT = Connector(log, Connector.new(socket.SOCK_STREAM, 2, self.rtPort, self.rtAddr))
            if conRT.tryConnect((relayAddr, relayPort)):
                conRT.sendall(data)
                conRT.setKeepAlive()
                break
            else:
                conRT = None

        if conRT:
            self.conRT       = conRT
            self.allowSelect = True
            for ep in self.eps:
                if ep is not self.epControl:
                    ep.allowSelect = True
            self.state = self.States.WaitReady


    # Needed for select()
    def fileno(self):
        return self.conRT.fileno()


    # Called after select()
    def task(self):
        if   self.state == self.States.Disconnected: assert False # should not ever be called
        elif self.state == self.States.WaitReady:    self.taskReady()
        elif self.state == self.States.Forwarding:   self.taskForward()


    def taskReady(self):
        data = self.conRT.tryRecv(64)
        if data is None:
            return
        if len(data) == 64:
            # Confirmation
            return
        if   data == b'Ready !\n': self.secureForward()
        elif data == b'Bad T !\n': self.disconnect()
        else:                      self.reconnect()


    def taskForward(self):

        data = self.conRT.tryRecv(32768)
        if data is None:
            return
        if len(data) < 1:
            self.reconnect()
            return

        self.buffer += data

        while len(self.buffer) >= 4:

            header = self.buffer[0:4]
            totalLen = int.from_bytes(header[0:2], 'little') + 4
            epID     = int.from_bytes(header[2:4], 'little')

            # Check if we need more bytes to complete the packet
            if totalLen > len(self.buffer):
                break

            ep = self.eps[epID]
            if ep:
                ep.acceptMessage(self.buffer[4:totalLen])
            else:
                log.info(t('Channel\t [{0:5d}] not found'.format(epID)))

            self.buffer = self.buffer[totalLen:]


    # Called by ChannelEndpoint,
    # sends <packet> through the link to the remote portal.
    def sendPacket(self, packet):
        try:
            self.conRT.socket.settimeout(2)
            self.conRT.sendall(packet)
            self.conRT.socket.settimeout(0)
        except OSError as e:
            log.error(e)
            self.reconnect()


    # Functions called by control channel and listeners

    def reserveChannel(self, listener):
        channel            = ChannelPlaceholder(-1, -1, self)
        channel.myListener = listener
        channelID          = self.eps.append(channel)
        channel.myID       = channelID
        return channelID


    def addChannel(self, channelIDF, conn):

        if not conn:
            return 0

        channel      = ChannelData(-1, channelIDF, self, conn)
        channelID    = self.eps.append(channel)
        channel.myID = channelID

        return channelID


    def newChannel(self, channelIDF, devicePort, deviceAddr):

        for i in range(3):
            conn = Connector(logEP, Connector.new(socket.SOCK_STREAM, 2, self.ltPort, self.ltAddr))
            if conn.tryConnect((deviceAddr, devicePort)):
                return self.addChannel(channelIDF, conn)

        return 0


    def upgradeChannel(self, channelID, channelIDF, channelSocket):

        conn = Connector(logEP, channelSocket)

        ep = self.eps[channelID]
        if not isinstance(self.eps[channelID], ChannelPlaceholder):
            return False

        #self.eps[channelID].close()
        self.eps[channelID] = ChannelData(channelID, channelIDF, self, conn)

        return True


    # Accept local connection
    # by calling accept() on the listener (= socket accept)
    # that corresponds to the channelID
    def acceptChannel(self, channelID, channelIDF):
        try:
            listener = self.eps[channelID].myListener
            return listener.accept(channelID, channelIDF)
        except (IndexError, AttributeError):
            return False


    # Accept local connection
    # by calling decline() on the listener (= socket accept and close immediately)
    # that corresponds to the channelID
    def declineChannel(self, channelID, channelIDF):
        try:
            listener = self.eps[channelID].myListener
            return listener.decline()
        except (IndexError, AttributeError):
            return False


    def deleteChannel(self, channelID):
        try:
            self.eps[channelID].close()
            del self.eps[channelID]
            return True
        except (IndexError, AttributeError):
            return False

