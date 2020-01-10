
import time
import logging
import socket
import select

import Globals
import ConfigFields as CF

from Common.Generic  import find
from Common.SlotList import SlotList
from Common.AsyncConnectorPacketized \
    import  AsyncConnectorPacketized
from Common.Promises import Promises
from Common.Loop     import EventAsync, loop
from .Link           import Link
from .Portal_log     import LogClass, Etypes

log = logging.getLogger(__name__ + '  ')

class Portal:

    def __init__(self, portalID, serverPort, serverAddr, port=0, address='0.0.0.0'):
        self.log          = Globals.logger.new(LogClass)
        self.portalID     = portalID
        self.serverPort   = serverPort
        self.serverAddr   = serverAddr
        self.port         = port
        self.address      = address
        self.links        = SlotList()
        self.connect      = EventAsync(self._connect)
        self.conST        = None
        self.promises     = Promises(Globals.timeoutReminder)
        self.waitingSince = 0
        self.reminderRX   = Globals.kaReminderRX.new(owner=self, onRun=Portal.handleRemindRX, enabled=False)
        self.reminderTX   = Globals.kaReminderTX.new(owner=self, onRun=Portal.handleRemindTX, enabled=True)
        self.log(Etypes.Inited, portalID, serverPort, serverAddr, port, address)

    def teardown(self):
        self.promises.dropAll()
        for link in self.links:
            link.teardown()
        self.links    = None
        self.connect  = None

# Main

    def main(self):
        Globals.logPrint('.', end='')
        Globals.runReminders()
        self.runConnect()
        activeR, canWakeR = Globals.readables.get()
        activeW, canWakeW = Globals.writables.get()
        wokeR,  wokeW,  _ = select.select(canWakeR, canWakeW, [], 5)
        readyR, readyW, _ = select.select(activeR,  activeW,  [], 0)
        Globals.readables.selected(readyR, (readyR, readyW))
        Globals.writables.selected(readyW, (readyR, readyW))
        for link in self.links:
            link.task(readyR, readyW)

# Connect

    def runConnect(self):
        if not self.connect.isPendingOrComplete():
            now = time.time()
            if now > self.waitingSince + 5:
                self.waitingSince = now
                loop.run(self.connect())

    async def _connect_p1(self):
        conST = await self._connectToServer()
        if not conST:
            return False
        conST.setKeepAlive()
        ok = await self._authenticate(conST)
        if not ok:
            return False
        self.conST = conST
        self.reminderRX.skipNext = True
        self.reminderRX.enabled  = True
        loop.run(self.rtask())
        return True

    async def _connect(self):
        self.log(Etypes.Connect)
        result = await self._connect_p1()
        self.log(Etypes.ConnectResult, result)
        return result

    async def _connectToServer(self):
        conST = AsyncConnectorPacketized(
                    Globals.readables,
                    Globals.writables,
                    new=(socket.SOCK_STREAM, 0, self.port, self.address)
                )
        if not await conST.tryConnectAsync((self.serverAddr, self.serverPort)): return None
        conST.secureClient(serverHostname='server', caFilename='server.cer')
        if not await conST.tryDoHandshakeAsync():                               return None
        return conST

    async def _authenticate(self, conST):
        data  = b'V0.1'
        data += b'AUTH'
        data += self.portalID
        if not await conST.sendPacketAsync(data): return False
        reply = await conST.recvPacketAsync()
        return reply == b'V0.1REPL.OK.'

    # To be called only by rtask()
    def disconnect(self):
        assert self.connect.isComplete() # TODO: remove
        self.log(Etypes.Disconnect)
        self.connect.reset()
        self.conST.tryClose()
        self.conST = None
        self.reminderRX.enabled = False

# Keepalives

    def handleRemindRX(self):
        if self.connect.isComplete():
            log.warn('RX keepalive timeout')
            self.conST.tryShutdown(True, True)

    def handleRemindTX(self):
        if self.connect.isComplete():
            loop.run(self.requestKA())

# Send

    async def send(self, data):
        self.reminderTX.skipNext = True
        ok = await self.connect()
        if not ok:
            return False
        return await self.conST.sendPacketAsync(data)

# Receive task

    async def rtask(self):
        while True:
            packet = await self.conST.recvPacketAsync()
            if packet is None: continue
            if not packet:
                log.warn('Server disconnected us')
                break
            self.reminderRX.skipNext = True
            try:
                reply = self.process(packet)
            except AssertionError:
                log.warn('Bad packet')
                break
            if reply:
                if not await self.send(reply): break
        self.disconnect()

    def process(self, packet):
        assert len(packet) >= 8
        ref   = packet[0:4]
        reqID = int.from_bytes(ref, 'little')
        cmd   = packet[4:8]
        data  = packet[8:]
        repl  = ref
        repl += b'REPL'
        if   cmd == b'REPL':
            # Reply
            self.promises.fire(reqID, (data,))
            return None
        elif cmd == b'CLKR':
            ret = self.processCLKR(data)
            if ret is None:
                return None
            else:
                repl += ret
        else:
            assert False
        return repl

    # Create link via relay
    def processCLKR(self, data):
        assert len(data) > 26
        otherID    = data[ 0: 4]
        otherIDV   = data[ 4: 8]
        otherUser  = data[ 8:12]
        otherUserV = data[12:16]
        token      = data[16:24]
        relayPort  = int.from_bytes(data[24:26], 'little')
        relayAddr  = str(data[26:], 'utf-8')
        link       = self.createLink(False, otherID, otherIDV, otherUser, otherUserV)
        ok         = link.connectToRelay(token, relayPort, relayAddr)
        # data[ 8:] = b'.OK.' if ok else b'.NK.'
        return None

    def requestRelayRR(self, data):
        if not data:
            return None
        assert len(data) >= 4
        ok = data[ 0: 4]
        if   ok == b'.OK.':
            assert len(data) > 26
            otherIDV   = data[ 4: 8]
            otherUser  = data[ 8:12]
            otherUserV = data[12:16]
            token      = data[16:24]
            relayPort  = int.from_bytes(data[24:26], 'little')
            relayAddr  = str(data[26:], 'utf-8')
            return otherIDV, otherUser, otherUserV, token, relayPort, relayAddr
        elif ok == b'NFND' or ok == b'NORL':
            return None
        else:
            assert False

    async def requestRelay(self, otherID):
        p      = self.promises.new(self.requestRelayRR)
        reqID  = p.myID
        data   = reqID.to_bytes(4, 'little')
        data  += b'RQRL'
        data  += otherID
        if not await self.send(data): return None
        return await loop.watch(p)

    async def requestKA(self):
        p      = self.promises.new()
        reqID  = p.myID
        data   = reqID.to_bytes(4, 'little')
        data  += b'.KA.'
        if not await self.send(data): return None
        return await loop.watch(p)

# Links

    def createLink(self, isClient, otherID, otherIDV=b'', otherUser=b'', otherUserV=b''):
        l = find(self.links, lambda lk: lk.otherID == otherID)
        if l:
            # Remove existing link, if it has different security info
            if l.otherIDV != otherIDV or l.otherUser != otherUser or l.otherUserV != otherUserV:
                self.removeLink(l.myID)
                l = None
        if not l:
            # TODO: allow for different binding port & address than self.port, self.address
            lID = self.links.append(0)
            l   = Link(isClient, lID, self, otherID, otherIDV, otherUser, otherUserV, self.port, self.address, self.port, self.address)
            self.links[lID] = l
        return l

    def removeLink(self, linkID):
        l = self.links.pop(linkID)
        if l:
            l.teardown()

# API

    fields = [
        # Name,         Type,          Readable, Writable
        ('portalID',    CF.PortalID(), True,     False),
        ('serverPort',  CF.Port(),     True,     True),
        ('serverAddr',  CF.Address(),  True,     True),
        ('port',        CF.Port(),     True,     True),
        ('address',     CF.Address(),  True,     True),
        ('links',       CF.SlotList(), True,     True),
        # Functions
        ('createLink', CF.Call(createLink, [
            ('isClient', CF.Bool()),
            ('otherID',  CF.PortalID())
        ]), False, True),
        ('removeLink', CF.Call(removeLink, [
            ('linkID', CF.Int())
        ]), False, True)
    ]

