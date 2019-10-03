
import logging
import socket
import time

from enum import Enum

import Globals
import ConfigFields as CF

from Common.SmartTabs import t
from Common.SlotList  import SlotList
from Common.Connector import Connector

from .ChannelEndpoint import ChannelEndpoint, ChannelPlaceholder
from .ChannelControl  import ChannelControl
from .ChannelData     import ChannelData
from .Listener        import Listener

log   = logging.getLogger(__name__ + '    ')
logEP = logging.getLogger(__name__ + ' :EP')

class Etypes(Enum):
    Inited  = 0
    Deleted = 1

class Link:

    class States(Enum):
        Disconnected = 0
        WaitReady    = 1
        Forwarding   = 2

    fields = [
        # Name,          Type,            Readable, Writable
        # ('myID',         CF.Int(),        True,     False),
        ('isClient',     CF.Bool(),       True,     True),
        ('otherID',      CF.PortalID(),   True,     True),
        ('rtPort',       CF.Port(),       True,     True),
        ('rtAddr',       CF.Address(),    True,     True),
        ('ltPort',       CF.Port(),       True,     True),
        ('ltAddr',       CF.Address(),    True,     True),
        ('state',        CF.Enum(States), True,     True),
        ('waitingSince', CF.Float(),      True,     True),
        ('kaCountIdle',  CF.Int(),        True,     True),
        ('buffer',       CF.Hex(),        True,     True),
        ('listeners',    CF.SlotList(),   True,     True),
        ('eps',          CF.SlotList(),   True,     True)
    ]

    def __init__(self, isClient, myID, myPortal, otherID, rtPort=0, rtAddr='0.0.0.0', ltPort=0, ltAddr='0.0.0.0'):

        self.isClient      = isClient
        self.myID          = myID
        self.myPortal      = myPortal
        self.otherID       = otherID
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
        self.onConnected   = []
        self.reminderRX    = Globals.kaReminderRX.getDelegate(onRun={ self.handleRemindRx })
        self.reminderTX    = Globals.kaReminderTX.getDelegate(onRun={ self.handleRemindTx })
        self.kaCountIdle   = 0
        self.readable      = Globals.readables.new(self, isActive=False, canWake=True)
        self.writable      = Globals.writables.new(self, isActive=False, canWake=True)

        self.waitingSince  = 0

        self.log           = Globals.logger.new(Globals.LogTypes.Link)
        self.log(Etypes.Inited, (isClient, myID, otherID, rtPort, rtAddr, ltPort, ltAddr))


    def __del__(self):
        self.log(Etypes.Deleted, ())


    def isIdle(self):
        return self.kaCountIdle > 3 and not self.onConnected and len(self.eps) <= 1

    def handleRemindRx(self):
        if self.state != self.States.Disconnected:
            self.connectionLost('RX keepalive timeout')
        return False

    def handleRemindTx(self):
        self.kaCountIdle += 1
        if self.state == self.States.Forwarding:
            self.epControl.sendKA()
        return False


    def connectionLost(self, reason='N/A'):
        log.warn('Connection lost, reason: {0}'.format(reason))
        if self.isIdle():
            log.warn('Disconnecting')
            self.disconnect()
        else:
            log.warn('Reconnecting')
            self.reconnect()


    def addListener(self, remotePort, remoteAddr, localPort, localAddr):
        listener      = Listener(-1, self, remotePort, remoteAddr, localPort, localAddr)
        listenerID    = self.listeners.append(listener)
        listener.myID = listenerID
        return listener

    def removeListener(self, listenerID):
        del self.listeners[listenerID]


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
            hs = self.conRT.doHandshake()
            if hs == Connector.HandshakeStatus.OK:
                self.conRT.socket.settimeout(0)
                self.state = self.States.Forwarding
                self.waitingSince = 0
                self.kaCountIdle = 0
                self.reminderRX.skipNext = True
        except OSError as e:
            log.error(e)
            self.reconnect()
        else:
            self.connected(True)


    def disconnect(self):
        self.conRT.tryClose()
        self.conRT = None
        self.readable.off()
        self.writable.off()
        self.state = self.States.Disconnected


    def reconnect(self):
        self.disconnect()
        self.requestConnect()


    def requestConnect(self):
        if self.isClient:
            now = time.time()
            if now > self.waitingSince + 2:
                self.waitingSince = now
                self.myPortal.connectToPortal(self.otherID)


    def connected(self, ok):
        handlers = self.onConnected
        self.onConnected = []
        for handler in handlers:
            handler(ok)


    def connectAndCall(self, f):
        if self.state == self.States.Forwarding:
            f(True)
        else:
            self.onConnected.append(f)
            self.requestConnect()


    def connectToRelay(self, token, relayPort, relayAddr):

        if self.conRT:
            self.disconnect()

        data = token + b'0' * 56

        for i in range(3):
            conRT = Connector(new=(socket.SOCK_STREAM, 2, self.rtPort, self.rtAddr))
            if conRT.tryConnect((relayAddr, relayPort)):
                conRT.sendall(data)
                # conRT.setKeepAlive()
                break
            else:
                conRT = None

        if conRT:
            self.conRT = conRT
            self.readable.on()
            self.writable.on()
            self.state = self.States.WaitReady
            self.reminderRX.skipNext = True
        else:
            self.connected(False)


    # Needed for select()
    def fileno(self):
        return self.conRT.fileno()


    def rtask(self, readables, writables):
        if   self.state == self.States.Disconnected: assert False # should not ever be called
        elif self.state == self.States.WaitReady:    self.taskReady()
        elif self.state == self.States.Forwarding:   self.taskForward()


    def wtask(self, readables, writables):
        if self.state == self.States.Forwarding:
            for ep in self.eps:
                if ep in readables:
                    ep.rtask()


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

        self.reminderRX.skipNext = True

        data = self.conRT.tryRecv(32768)
        if data is None:
            return
        if len(data) < 1:
            self.connectionLost('Closed by other end')
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
    def sendPacket(self, packet, untracked=False):
        if not untracked:
            self.reminderTX.skipNext = True
            self.kaCountIdle = 0
        if self.state == self.States.Forwarding:
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
            conn = Connector(new=(socket.SOCK_STREAM, 2, self.ltPort, self.ltAddr))
            if conn.tryConnect((deviceAddr, devicePort)):
                conn.socket.settimeout(0)
                return self.addChannel(channelIDF, conn)

        return 0


    def upgradeChannel(self, channelID, channelIDF, channelSocket):

        conn = Connector(channelSocket)

        ep = self.eps[channelID]
        if not isinstance(self.eps[channelID], ChannelPlaceholder):
            return False

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
        if channelID > 0:
            try:
                del self.eps[channelID]
                return True
            except (IndexError, AttributeError):
                return False


    fields.extend([
        ('addListener', CF.Call(addListener, [
            ('remotePort', CF.Port(),    False, False),
            ('remoteAddr', CF.Address(), False, False),
            ('localPort',  CF.Port(),    False, False),
            ('localAddr',  CF.Address(), False, False)
        ]), False, True),
        ('removeListener', CF.Call(removeListener, [
            ('listenerID', CF.Int(), False, False)
        ]), False, True),
        ('deleteChannel', CF.Call(deleteChannel, [
            ('channelID', CF.Int(), False, False)
        ]), False, True)
    ])

