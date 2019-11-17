
import logging
import socket

import Globals
import ConfigFields as CF

from Common.SlotList       import SlotList
from Common.Connector      import Connector
from Common.AsyncConnector import AsyncConnector
from Common.Async          import EventAsync, loop
from .Channels             import Channels
from .Listener             import Listener
from .Link_log             import LogClass, Etypes

log   = logging.getLogger(__name__ + '    ')
logEP = logging.getLogger(__name__ + ' :EP')

class Link:

    def __init__(self, isClient, myID, myPortal, otherID, rtPort, rtAddr, ltPort, ltAddr):
        self.log           = Globals.logger.new(LogClass)
        self.isClient      = isClient
        self.myID          = myID
        self.myPortal      = myPortal
        self.otherID       = otherID
        self.rtPort        = rtPort
        self.rtAddr        = rtAddr
        self.listeners     = SlotList()
        self.channels      = Channels(self, ltPort, ltAddr)
        self.buffer        = b''
        self.connect       = EventAsync(self._connect)
        self.conRT         = None
        self.reminderRX    = Globals.kaReminderRX.new(enabled=False, onRun=self.handleRemindRX)
        self.reminderTX    = Globals.kaReminderTX.new(enabled=False, onRun=self.handleRemindTX)
        self.kaCountIdle   = 0
        self.readable      = Globals.readables.new(self, isActive=False, canWake=True)
        self.writable      = Globals.writables.new(self, isActive=False, canWake=False)
        self.log(Etypes.Inited, isClient, myID, otherID, rtPort, rtAddr, ltPort, ltAddr)

    def teardown(self):
        self.channels.teardown()
        self.listeners = None
        self.channels  = None
        self.connect   = None

    # Needed for select()
    def fileno(self):
        return self.conRT.fileno()

# Connect

    async def _connect(self, info=None):
        clientSide = info is None
        if clientSide:
            if not self.isClient:
                return False
            info = await self.myPortal.requestRelay(self.otherID)
            if not info:
                return False
        conRT = await self._connectViaRelay(*info)
        if not conRT:
            return False
        conRT = await self._secureForward(conRT, clientSide)
        if not conRT:
            return False
        self.conRT = Connector(fromSocket=conRT.socket)
        self.readable.on()
        self.writable.on()
        self.kaCountIdle         = 0
        self.reminderRX.skipNext = True
        self.reminderRX.enabled  = True
        return True

    def connectToRelay(self, token, relayPort, relayAddr):
        # Todo: uncomment isIdle() condition
        # if self.isIdle():
        self.disconnect()
        loop.run(self.connect(info=(token, relayPort, relayAddr)))
        return True
        # else:
        #     return False

    async def _connectViaRelay(self, token, relayPort, relayAddr):
        data = token + b'0' * 56
        conRT = AsyncConnector(
            Globals.readables,
            Globals.writables,
            new=(socket.SOCK_STREAM, 0, self.rtPort, self.rtAddr)
        )
        if not await conRT.tryConnectAsync((relayAddr, relayPort)): return None
        if not await conRT.trySendallAsync(data):                   return None
        reply = await conRT.tryRecvAsync(64)
        if reply != data:                                           return None
        reply = await conRT.tryRecvAsync(8)
        if reply != b'Ready !\n':                                   return None
        return conRT

    async def _secureForward(self, conRT, clientSide):
        try:
            if clientSide:
                conRT.secureClient(serverHostname='portal', caFilename='portal.cer')
            else:
                conRT.secureServer(certFilename='portal.cer', keyFilename='portal.key')
            ok = await conRT.doHandshakeAsync()
            if ok:
                return conRT
        except OSError as e:
            log.error(e)
        return None

    def disconnect(self):
        if self.connect.isComplete():
            self.connect.reset()
            self.conRT.tryClose()
            self.conRT = None
            self.readable.off()
            self.writable.off()

    async def reconnect(self):
        self.disconnect()
        return await self.connect()

    def isIdle(self):
        return \
            not self.connect.isPending() \
            and (
                not self.connect.isComplete() \
                or  self.kaCountIdle > 3 and self.channels.isEmpty()
            )

    def connectionLost(self, reason='N/A'):
        log.warn('Connection lost, reason: {0}'.format(reason))
        if self.isIdle():
            log.warn('Disconnecting')
            self.disconnect()
        else:
            log.warn('Reconnecting')
            loop.run(self.reconnect())

# Keepalives

    def handleRemindRX(self):
        if self.connect.isComplete():
            self.connectionLost('RX keepalive timeout')

    def handleRemindTX(self):
        self.kaCountIdle += 1
        if self.connect.isComplete():
            self.epControl.sendKA()

# Listeners

    def addListener(self, remotePort, remoteAddr, localPort, localAddr):
        try:
            lID = self.listeners.append(0)
            l   = Listener(lID, self, remotePort, remoteAddr, localPort, localAddr)
            self.listeners[lID] = l
            return l
        except OSError:
            return None

    def removeListener(self, listenerID):
        del self.listeners[listenerID]

    async def requestChannel(self, remotePort, remoteAddr):
        ok = await self.connect()
        log.warn(f'ok = {ok}')
        if ok:
            return await self.channels.requestChannel(remotePort, remoteAddr)
        else:
            return None

    def upgradeChannel(self, channelID, channelIDF, connSocket):
        return self.channels.upgradeChannel(channelID, channelIDF, connSocket)

    def deleteChannel(self, channelID):
        return self.channels.deleteChannel(channelID)

# Task

    def yesWakeW(self):
        self.writable.yesWake()
        # self.channels.noWake() ?
    def noWakeW(self):
        self.writable.noWake()
        # self.channels.yesWake() ?

    def task(self, readyR, readyW):
        if self in readyR:
            self.rtask(readyW)
        if self in readyW:
            self.wtask(readyR)
        else:
            self.yesWakeW()
        for listener in self.listeners:
            if listener in readyR:
                listener.rtask()

    def rtask(self, readyW):
        self.reminderRX.skipNext = True
        if self.connect.isComplete():
            cap = 32768 - len(self.buffer)
            if cap < 16384:
                return
            data = self.conRT.tryRecv(cap)
            if data is None:
                return
            if len(data) < 1:
                self.connectionLost('Closed by other end')
                return
            self.buffer += data
            while len(self.buffer) >= 4:
                header    = self.buffer[0:4]
                totalLen  = int.from_bytes(header[0:2], 'little') + 4
                channelID = int.from_bytes(header[2:4], 'little')
                # Check if we need more bytes to complete the packet
                if totalLen > len(self.buffer):
                    break
                self.channels.acceptMessage(channelID, self.buffer[4:totalLen])
                self.buffer = self.buffer[totalLen:]

    def send(self, data):
        self.reminderTX.skipNext = True
        self.kaCountIdle = 0
        try:
            self.conRT.sendall(data)
        except OSError as e:
            log.error(e)
            self.reconnect()

    def wtask(self, readyR):
        if self.connect.isComplete():
            data = self.channels.readAll(readyR)
            if data:
                self.send(data)
            else:
                self.noWakeW()


    fields = [
        # Name,          Type,          Readable, Writable
        # ('myID',         CF.Int(),      True,     False),
        ('isClient',     CF.Bool(),     True,     True),
        ('otherID',      CF.PortalID(), True,     True),
        ('rtPort',       CF.Port(),     True,     True),
        ('rtAddr',       CF.Address(),  True,     True),
        ('kaCountIdle',  CF.Int(),      True,     True),
        ('buffer',       CF.Hex(),      True,     True),
        ('listeners',    CF.SlotList(), True,     True),
        # Functions
        ('addListener', CF.Call(addListener, [
            ('remotePort', CF.Port()),
            ('remoteAddr', CF.Address()),
            ('localPort',  CF.Port()),
            ('localAddr',  CF.Address())
        ]), False, True),
        ('removeListener', CF.Call(removeListener, [
            ('listenerID', CF.Int())
        ]), False, True)
    ]

