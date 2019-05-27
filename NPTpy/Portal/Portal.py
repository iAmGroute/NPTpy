
import logging
import socket
import select
import time

from Common.Connector       import Connector
from Common.SecureConnector import SecureClientConnector

from .Link import Link

log = logging.getLogger(__name__)

class Portal:

    def __init__(self, isClient, portalID, serverPort, serverAddr, port=0, address='0.0.0.0'):
        self.isClient    = isClient
        self.portalID    = portalID
        self.serverPort  = serverPort
        self.serverAddr  = serverAddr
        self.port        = port
        self.address     = address
        self.links       = []
        self.conST       = None
        self.allowSelect = True


    # Needed for select()
    def fileno(self):
        return self.conST.fileno()


    def main(self):

        if not self.conST:
            self.connectKA()

        else:

            for link in self.links:
                if link:
                    link.maintenance()

            socketList = [self]
            for link in self.links:
                if link:
                    socketList.append(link)
                    socketList.extend(link.listeners)
                    socketList.extend(link.eps[1:])
            socketList = [s for s in socketList if s and s.allowSelect]

            readable, writable, exceptional = select.select(socketList, [], [])
            for s in readable:
                s.task()


    def connectKA(self):
        self.conST = SecureClientConnector(log, Connector.new(socket.SOCK_STREAM, 2, self.port, self.address))
        self.conST.secure(serverHostname='server', caFilename='server.cer')
        data = b''
        data += self.portalID
        data += b'0' * 60
        if not self.conST.tryConnect((self.serverAddr, self.serverPort), data):
            self.conST = None
            time.sleep(10)
            return
        self.conST.socket.settimeout(None)


    def task(self):

        relayInfo = self.conST.tryRecv(1024)
        l = len(relayInfo)
        if l < 11:
            if l == 0: self.conST = None
            return

        token     = relayInfo[0:8]
        relayPort = int.from_bytes(relayInfo[8:10], 'little')
        relayAddr = str(relayInfo[10:], 'utf-8')

        # TODO: allow for different binding port & address than self.port, self.address
        # and provide the remote portal's ID instead of the token/relay info
        link = Link(self.isClient, len(self.links), self, token, relayPort, relayAddr, self.port, self.address)
        self.links.append(link)


    def removeLink(self, linkID):
        self.links[linkID] = None


    # 'Client' mode
    # Notice that the behaviour of the server is symmetric
    # with respect to who is the client and who the portal,
    # so sending a request will trigger the same response to both sides.
    # Therefore, we can simply 'inject' a connect message
    # and the remaining will be handled automatically.
    def connectToPortal(self, otherID):
        if not self.conST:
            return
        methodID = 1
        data =  methodID.to_bytes(4, 'little')
        data += otherID
        data += b'0' * 56
        self.conST.sendall(data)

