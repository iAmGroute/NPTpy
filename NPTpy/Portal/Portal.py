
import logging
import socket
import select

from Common.Connector import Connector

from .Link import Link

log = logging.getLogger(__name__)

ServerAddr = '127.0.0.1'
ServerPort = 4020

class Portal:

    def __init__(self, portalID, port=0, address='0.0.0.0'):
        self.portalID = portalID
        self.port     = port
        self.address  = address
        self.links    = []
        self.conST    = None
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
        self.conST = Connector(log, Connector.new(socket.SOCK_STREAM, 2, self.port, self.address))
        data = b''
        data += self.portalID
        data += b'0' * 60
        if not self.conST.tryConnect((ServerAddr, ServerPort), data):
            self.conST = None


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
        link = Link(len(self.links), self, token, relayPort, relayAddr, self.port, self.address)
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


    # def keepaliveTask(self, serverEP, primary=True):
    #     data = b'0000' + portalID.to_bytes(4, 'little') + b'0000'
    #     code = 0x5A if primary else 0x5B # backup
    #     i = 0
    #     while True:
    #         # Register message every 4 messages
    #         # the other 3 are ignored by the server,
    #         # but keep the NAT happy.
    #         data[0] = code if (i % 4) == 0 else 0x00
    #         # TODO: grenerate OTP
    #         #data[8:12] = --- new OTP ---
    #         # TODO: add primary server's GUID/url if primary == False
    #         self.con.sendto(data, serverEP)
    #         time.sleep(4)

    # def listen(self):
    #     data, addr = self.con.recvfrom(256)
    #     header = data[0:4]
    #     otp    = data[4:8]

    #     # TODO: verify otp

    #     if header == b'CONN':
    #         self.connect()
    #     elif header == b'CONT':
    #         serverURL = str(data[8:], 'utf-8')
    #         self.connect(serverURL)

    #     # TODO: add dead timer countdown for server
    #     # reset the countdown
