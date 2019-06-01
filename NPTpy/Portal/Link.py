
import logging
import socket

from Common.Connector       import Connector
from Common.SecureConnector import SecureClientConnector
from Common.SecureConnector import SecureServerConnector
from Common.SlotList        import SlotList

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


    def __init__(self, isClient, myID, myPortal, myToken, relayPort, relayAddr, rtPort=0, rtAddr='0.0.0.0', ltPort=0, ltAddr='0.0.0.0'):

        self.isClient    = isClient
        self.myID        = myID
        self.myPortal    = myPortal
        self.myToken     = myToken
        self.relayPort   = relayPort
        self.relayAddr   = relayAddr
        self.rtPort      = rtPort
        self.rtAddr      = rtAddr
        self.ltPort      = ltPort
        self.ltAddr      = ltAddr

        self.listeners   = []

        self.epControl   = ChannelControl(0, 0, self)
        self.eps         = SlotList(4, [self.epControl])
        assert self.eps[0] is self.epControl

        self.buffer      = b''
        self.state       = self.States.Disconnected
        self.conRT       = None
        self.allowSelect = False


    def addListener(self, devicePort, deviceAddr, port, address):
        listener = Listener(len(self.listeners), self, devicePort, deviceAddr, port, address)
        self.listeners.append(listener)


    def close(self):
        self.conRT.tryClose()
        self.conRT       = None
        self.allowSelect = False
        for i in range(len(self.eps.slots)):
            ep = self.eps.slots[i].val
            if ep:
                ep.close()
            self.eps.deleteByIndex(i)
        for i in range(len(self.listeners)):
            listener = self.listeners[i]
            if listener:
                listener.close()
            self.listeners[i] = None


    def removeEP(self, channelID):
        ep = self.eps[channelID]
        if ep:
            del self.eps[channelID]
            self.epControl.requestDeleteChannel(channelID, ep.myIDF)


    def maintenance(self):
        if not self.conRT:
            self.taskConnect()


    def secureForward(self):
        try:
            if self.isClient:
                self.conRT.secure(serverHostname='portal', caFilename='portal.cer')
            else:
                self.conRT.secure(certFilename='portal.cer', keyFilename='portal.key')
            self.state = self.States.Forwarding
        except OSError as e:
            log.error(error)
            self.reconnect()


    def reconnect(self):
        self.conRT.tryClose()
        self.conRT       = None
        self.allowSelect = False
        self.state = self.States.Disconnected
        self.taskConnect()


    def disconnect(self):
        self.state = self.States.Disconnected
        self.close()
        self.myPortal.removeLink(self.myID)


    # Needed for select()
    def fileno(self):
        return self.conRT.fileno()


    # Called after select()
    def task(self):
        if   self.state == self.States.Disconnected: assert False # self.taskConnect() # should not ever be called
        elif self.state == self.States.WaitReady:    self.taskReady()
        elif self.state == self.States.Forwarding:   self.taskForward()


    def taskConnect(self):

        assert not self.conRT

        data = self.myToken + b'0' * 56

        for i in range(3):

            if self.isClient:
                conRT = SecureClientConnector(log, Connector.new(socket.SOCK_STREAM, 2, self.rtPort, self.rtAddr))
            else:
                conRT = SecureServerConnector(log, Connector.new(socket.SOCK_STREAM, 2, self.rtPort, self.rtAddr))

            if conRT.tryConnect((self.relayAddr, self.relayPort)):
                conRT.sendall(data)
                conRT.setKeepAlive()
                break
            else:
                conRT = None

        if conRT:
            self.conRT       = conRT
            self.allowSelect = True
            self.state = self.States.WaitReady


    def taskReady(self):
        data = self.conRT.tryRecv(8)
        if   data == b'Ready !\n': self.secureForward()
        elif data == b'Bad T !\n': self.disconnect()
        else:                      self.reconnect()


    def taskForward(self):

        data = self.conRT.tryRecv(32768)
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
                log.warn('    epID not found')

            self.buffer = self.buffer[totalLen:]


    # Called by ChannelEndpoint,
    # sends <packet> through the link to the remote portal.
    def sendPacket(self, packet):
        try:
            self.conRT.sendall(packet)
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
            return -1

        channel      = ChannelData(-1, channelIDF, self, conn)
        channelID    = self.eps.append(channel)
        channel.myID = channelID

        return channelID


    def newChannel(self, channelIDF, devicePort, deviceAddr):

        for i in range(3):
            conn = Connector(logEP, Connector.new(socket.SOCK_STREAM, 2, self.ltPort, self.ltAddr))
            if conn.tryConnect((deviceAddr, devicePort)):
                conn.socket.settimeout(None)
                break
            else:
                conn.tryClose()
                conn = None

        return self.addChannel(channelIDF, conn)


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
            return listener.decline(channelID, channelIDF)
        except (IndexError, AttributeError):
            return False


    def deleteChannel(self, channelID):
        try:
            self.eps[channelID].close()
            self.eps[channelID] = None
            return True
        except (IndexError, AttributeError):
            return False

