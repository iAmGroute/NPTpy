
import logging
import socket
import select
from enum import Enum

from Common.Connector import Connector

log   = logging.getLogger(__name__ + '   ')
logST = logging.getLogger(__name__ + ':ST')
logRT = logging.getLogger(__name__ + ':RT')
logDV = logging.getLogger(__name__ + ':DV')

ServerAddr = '127.0.0.1'
ServerPort = 4020


class DeviceConn(Connector):
    index = -1
    conRT = None


class RelayConnector(Connector):
    class States(Enum):
        Disconnected = 0
        WaitClient   = 1
        Connecting   = 2
        Ready        = 3

    state  = States.Disconnected
    parent = None
    index  = -1
    conn   = None

    def task(self):
        if   self.state == self.States.Disconnected: return
        elif self.state == self.States.WaitClient:   self.waitReady()
        elif self.state == self.States.WaitClient:   self.connectTo()
        elif self.state == self.States.Ready:        self.forward()

    def connectRelay(self, token, relayPort, relayAddr):
        data = b''
        data += token
        data += b'0' * 56
        if self.tryConnect((relayAddr, relayPort), data):
            self.setKeepAlive()
            self.state = self.States.WaitClient
            return True
        else:
            return False

    def waitReady(self):
        data = self.tryRecv(8)
        if data == b'Ready !\n':
            self.state = self.States.Ready
        else:
            self.state = self.States.Disconnected
            self.tryClose()

    def connectTo(self):
        relayInfo = self.tryRecv(1024)
        l = len(relayInfo)
        if l < 11:
            if l == 0: self.conST = None
            return
        token     = relayInfo[0:8]
        relayPort = int.from_bytes(relayInfo[8:10], 'little')
        relayAddr = str(relayInfo[10:], 'utf-8')

        conRT = DeviceConn(logRT, socket.SOCK_STREAM, 2, self.port, self.address)
        for i in range(3):
            if conRT.connectRelay(token, relayPort, relayAddr):
                conRT.index = len(self.conRTs)
                conRT.parent = self
                self.conRTs.append(conRT)
                break
            else:
                conRT.tryClose()

    def forward(self):
        if self.conn:
            data = self.tryRecv(32768)
            if len(data) < 1:
                self.state = self.States.Disconnected
            self.sendall(data)

class Portal:

    def __init__(self, portalID, port=0, address='0.0.0.0'):
        self.portalID  = portalID
        self.port      = port
        self.address   = address
        self.conST     = None
        self.conRTs    = []
        self.conDVs    = []

    def main(self):
        if not self.conST:
            self.connectKA()
        else:
            socketList = [self.conST] + self.conRTs + self.conDVs
            socketList = filter(None, socketList)
            readable, writable, exceptional = select.select(socketList, [], [])
            for s in readable:
                if   s is self.conST: self.task()
                else:                 self.taskRT(s) # s is in self.conRTs or .conDVs

    def connectKA(self):
        self.conST = Connector(logST, socket.SOCK_STREAM, 2, self.port, self.address)
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

        conRT = RelayConnector(logRT, socket.SOCK_STREAM, 2, self.port, self.address)
        for i in range(3):
            if conRT.connectRelay(token, relayPort, relayAddr):
                conRT.parent = self
                conRT.index = len(self.conRTs)
                self.conRTs.append(conRT)
                break
            else:
                conRT.tryClose()

    def taskRT(self, conRT):
        conRT.task()
        if conRT.state == conRT.States.Disconnected:
            self.conRTs[conRT.index] = None

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
