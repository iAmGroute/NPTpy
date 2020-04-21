
import time
import logging
import socket
import select
import os

import Globals
import ConfigFields as CF

from LogPack         import logger, logPrint
from Common.Generic  import find
from Common.SlotList import SlotList
from Common.AsyncConnectorPacketized \
    import  AsyncConnectorPacketized
from Common.Futures  import Futures
from NextLoop        import loop
from .Link           import Link
from .Portal_log     import LogClass, Etypes

log = logging.getLogger(__name__ + '  ')

class Portal:

    def __init__(self, portalID, userID, serverPort, serverAddr, port=0, address='0.0.0.0'):
        self.log          = logger.new(LogClass)
        self.portalID     = portalID
        self.userID       = userID
        self.serverPort   = serverPort
        self.serverAddr   = serverAddr
        self.port         = port
        self.address      = address
        self.links        = SlotList()
        self.connect      = loop.newEvent(self._connect)
        self.conST        = None
        self.futures      = Futures(loop, Globals.timeoutReminder)
        self.waitingSince = 0
        self.reminderRX   = Globals.kaReminderRX.new(owner=self, onRun=Portal.handleRemindRX, enabled=False)
        self.reminderTX   = Globals.kaReminderTX.new(owner=self, onRun=Portal.handleRemindTX, enabled=True)
        self.log(Etypes.Inited, portalID, userID, serverPort, serverAddr, port, address)

    def teardown(self):
        self.futures.cancelAll()
        for link in self.links:
            link.teardown()
        self.links    = None
        self.connect  = None

# Main

    def main(self):
        logPrint('.', end='')
        Globals.runReminders()
        self.runConnect()
        activeR = Globals.readables.get()
        activeW = Globals.writables.get()
        readyR, readyW, _ = select.select(activeR, activeW, [], 5)
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
        conST.secure(
            serverSide   = False,
            requireCert  = True,
            peerHostname = 'server',
            certFilename = 'portal_cer.pem',
            keyFilename  = 'portal_key.pem',
            caFilename   = 'server_cer.pem'
        )
        if not await conST.tryDoHandshakeAsync():                               return None
        return conST

    async def _authenticate(self, conST):
        data  = b'V0.1'
        data += b'AUTH'
        data += self.portalID
        data += self.userID
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
            log.info('RX keepalive timeout')
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
                log.info('Server disconnected us')
                break
            self.reminderRX.skipNext = True
            try:
                self.process(packet)
            except AssertionError:
                log.info('Bad packet')
                break
        self.disconnect()

    def process(self, packet):
        assert len(packet) >= 8
        ref  = packet[0:4]
        cmd  = packet[4:8]
        data = packet[8:]
        if   cmd == b'REPL':
            # Reply
            reqID = int.from_bytes(ref, 'little')
            f     = self.futures.pop(reqID)
            f.ready(data)
        elif cmd == b'.KA.':
            pass
        elif cmd == b'CLKR':
            self.processCLKR(data)
        else:
            assert False

    # Create link via relay
    def processCLKR(self, data):
        assert len(data) > 34
        otherID    = data[ 0: 4]
        otherIDV   = data[ 4: 8]
        otherUser  = data[ 8:12]
        otherUserV = data[12:16]
        tokenP     = data[16:24]
        tokenR     = data[24:32]
        relayPort  = int.from_bytes(data[32:34], 'little')
        relayAddr  = str(data[34:], 'utf-8')
        link       = self.createLink(False, otherID, otherIDV, otherUser, otherUserV)
        link.connectToRelay(tokenP, tokenR, relayPort, relayAddr)
        return None

    def requestRelayRR(self, data):
        if not data:
            return None
        assert len(data) >= 4
        ok = data[ 0: 4]
        if   ok == b'.OK.':
            assert len(data) > 34
            otherIDV   = data[ 4: 8]
            otherUser  = data[ 8:12]
            otherUserV = data[12:16]
            tokenP     = data[16:24]
            tokenR     = data[24:32]
            relayPort  = int.from_bytes(data[32:34], 'little')
            relayAddr  = str(data[34:], 'utf-8')
            return otherIDV, otherUser, otherUserV, tokenP, tokenR, relayPort, relayAddr
        elif ok in [b'DENY', b'NFND', b'NORL']:
            self.log(Etypes.ReplyNotOK, ok)
            return None
        else:
            assert False
            return None

    async def requestRelay(self, otherID):
        f, fID = self.futures.new()
        data   = fID.to_bytes(4, 'little')
        data  += b'RQRL'
        data  += otherID
        data  += os.urandom(8) # seed for tokenP
        await self.send(data)
        reply  = await f
        return self.requestRelayRR(reply)

    async def requestKA(self):
        data  = b'....'
        data += b'.KA.'
        await self.send(data)

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
        ('userID',      CF.PortalID(), True,     False),
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

