
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
from Common.Async    import Promise, EventAsync, loop
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
        self.promises     = SlotList()
        self.waitingSince = 0
        self.log(Etypes.Inited, portalID, serverPort, serverAddr, port, address)

    def teardown(self):
        for link in self.links:
            link.teardown()
        self.links    = None
        self.connect  = None
        self.promises = None

# Main

    def main(self):
        self.runConnect()
        Globals.runReminders()
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

    async def _connect(self):
        conST = await self._connectToServer()
        if not conST:
            return False
        conST.setKeepAlive()
        ok = await self._authenticate(conST)
        if not ok:
            return False
        self.conST = conST
        loop.run(self.rtask())
        return True

    async def _connectToServer(self):
        conST = AsyncConnectorPacketized(
                    Globals.readables,
                    Globals.writables,
                    new=(socket.SOCK_STREAM, 0, self.port, self.address)
                )
        if not await conST.tryConnectAsync((self.serverAddr, self.serverPort)): return None
        conST.secureClient(serverHostname='server', caFilename='server.cer')
        if not await conST.doHandshakeAsync():                                  return None
        return conST

    async def _authenticate(self, conST):
        data  = b'V0.1'
        data += b'AUTH'
        data += self.portalID
        await conST.sendPacketAsync(data)
        reply = await conST.recvPacketAsync()
        return reply == b'V0.1REPL.OK.'

    def disconnect(self):
        assert self.connect.isComplete() # TODO: remove
        self.connect.reset()
        self.conST.tryClose()
        self.conST = None

# Receive task

    async def rtask(self):
        # wait for connect() to finish first,
        # because _connect() can call task() before it finishes
        await self.connect()
        while True:
            packet = await self.conST.recvPacketAsync()
            if not packet:
                log.warn('Server disconnected us')
                break
            try:
                reply = self.process(bytearray(packet))
            except AssertionError:
                log.warn('Bad packet')
                break
            if reply:
                await self.conST.sendPacketAsync(reply)
        self.disconnect()

    def process(self, data):
        l = len(data)
        assert l >= 8
        ref   = data[ 0: 4]
        reqID = int.from_bytes(ref, 'little')
        cmd   = data[ 4: 8]
        repl  = ref
        repl += b'REPL'
        if   cmd == b'REPL':
            # Reply
            # Find the promise of the reqID and resolve it
            p = self.promises[reqID]
            if p:
                self.promises[reqID] = None
                p(data[ 8:])
            return None
        elif cmd == b'CLKR':
            # Create link via relay
            assert l > 22
            otherID   = data[ 8:12]
            token     = data[12:20]
            relayPort = int.from_bytes(data[20:22], 'little')
            relayAddr = str(data[22:], 'utf-8')
            link      = self.createLink(False, otherID)
            ok        = link.connectToRelay(token, relayPort, relayAddr)
            # data[ 8:] = b'.OK.' if ok else b'.NK.'
            return None
        else:
            assert False
        return repl

    def requestRelayRR(self, data):
        assert len(data) >= 4
        ok = data[ 0: 4]
        if   ok == b'.OK.':
            assert len(data) > 14
            token     = data[ 4:12]
            relayPort = int.from_bytes(data[12:14], 'little')
            relayAddr = str(data[14:], 'utf-8')
            return token, relayPort, relayAddr
        elif ok == b'NFND' or ok == b'NORL':
            return None
        else:
            assert False

    async def requestRelay(self, otherID):
        ok = await self.connect()
        if not ok:
            return None
        p      = Promise(self.requestRelayRR)
        reqID  = self.promises.append(p)
        data   = reqID.to_bytes(4, 'little')
        data  += b'RQRL'
        data  += otherID
        await self.conST.sendPacketAsync(data)
        return await loop.watch(p)

# Links

    def createLink(self, isClient, otherID):
        l = find(self.links, lambda lk: lk.otherID == otherID)
        if not l:
            # TODO: allow for different binding port & address than self.port, self.address
            lID = self.links.append(0)
            l   = Link(isClient, lID, self, otherID, self.port, self.address, self.port, self.address)
            self.links[lID] = l
        return l

    def removeLink(self, linkID):
        del self.links[linkID]

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

