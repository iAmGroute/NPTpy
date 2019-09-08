
import logging
import socket
import select
import time

import ConfigFields as CF

from Common.Generic   import find
from Common.SlotList  import SlotList
from Common.Connector import Connector

from .Link import Link

log = logging.getLogger(__name__ + '  ')

class Portal:

    fields = [
        # Name,         Type,          Readable, Writable
        ('portalID',    CF.PortalID(), True,     False),
        ('serverPort',  CF.Port(),     True,     True),
        ('serverAddr',  CF.Address(),  True,     True),
        ('port',        CF.Port(),     True,     True),
        ('address',     CF.Address(),  True,     True),
        ('allowSelect', CF.Bool(),     True,     True),
        ('links',       CF.SlotList(), True,     True)
    ]

    def __init__(self, portalID, serverPort, serverAddr, port=0, address='0.0.0.0'):
        self.portalID    = portalID
        self.serverPort  = serverPort
        self.serverAddr  = serverAddr
        self.port        = port
        self.address     = address
        self.links       = SlotList(4)
        self.conST       = None
        self.allowSelect = True


    # Needed for select()
    def fileno(self):
        return self.conST.fileno()


    def main(self):

        if not self.conST:
            self.connectKA()

        else:

            # Temorary
            # TODO: add a SlotMap to which all selectables will be registred
            socketList = [self]
            for link in self.links:
                socketList.append(link)
                socketList.extend(link.listeners)
                socketList.extend(link.eps)
            socketList = [s for s in socketList if s.allowSelect]

            readable, writable, exceptional = select.select(socketList, [], [], 1)
            for s in readable:
                # Avoid race conditions by re-checking allowSelect
                if s.allowSelect:
                    s.task()


    def connectKA(self):
        self.conST = Connector(log, Connector.new(socket.SOCK_STREAM, 2, self.port, self.address))
        self.conST.secureClient(serverHostname='server', caFilename='server.cer')
        data = b''
        data += self.portalID
        data += b'0' * 60
        if not self.conST.tryConnect((self.serverAddr, self.serverPort)):
            self.conST = None
            time.sleep(10)
            return
        self.conST.sendall(data)
        self.conST.setKeepAlive()
        self.conST.socket.settimeout(0)


    def task(self):

        data = self.conST.tryRecv(1024)
        if data is None:
            return
        l = len(data)
        if l < 19:
            log.warn('Received {0} Bytes but expected at least 19'.format(l))
            self.conST = None
            return

        magic     = data[0:4]
        if magic != b'v0.1':
            log.warn('Server version mismatch, we: {0}, server: {1}'.format('v0.1', magic))
            self.conST = None
            return
        otherID   = data[4:8]
        token     = data[8:16]
        relayPort = int.from_bytes(data[16:18], 'little')
        relayAddr = str(data[18:], 'utf-8')

        link = self.createLink(False, otherID)
        link.connectToRelay(token, relayPort, relayAddr)


    def createLink(self, isClient, otherID):
        link = find(self.links, lambda lk: lk.otherID == otherID)
        if not link:
            # TODO: allow for different binding port & address than self.port, self.address
            link      = Link(isClient, -1, self, otherID, self.port, self.address)
            linkID    = self.links.append(link)
            link.myID = linkID
        return link

    def removeLink(self, linkID):
        del self.links[linkID]


    # 'Client' mode
    # Notice that the behaviour of the server is symmetric
    # with respect to who is the client and who the portal,
    # so sending a request will trigger the same response to both sides.
    # Therefore, we can simply 'inject' a connect message
    # and the remaining will be handled automatically.
    # Called by Link.requestConnect()
    def connectToPortal(self, otherID):
        if not self.conST:
            self.connectKA()
            return
        methodID = 1
        data =  methodID.to_bytes(4, 'little')
        data += otherID
        data += b'0' * 56
        self.conST.sendall(data)


    fields.extend([
        ('createLink', CF.Call(createLink, [
            ('isClient', CF.Bool(),     False, False),
            ('otherID',  CF.PortalID(), False, False)
        ]), False, True),
        ('removeLink', CF.Call(removeLink, [
            ('linkID', CF.Int(), False, False),
        ]), False, True)
    ])

