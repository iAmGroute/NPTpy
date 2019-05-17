
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
    conRT = None
    def task(self):
        data = self.tryRecv(32768)
        if len(data) < 1:
            self.conRT.disconnect()
            return
        self.conRT.sendall(data)


class RelayConnector(Connector):

    class Modes(Enum):
        Portal = 0
        Client = 1

    class States(Enum):
        Disconnected = 0
        WaitReady    = 1
        WaitDevice   = 2
        Ready        = 3

    mode   = Modes.Portal
    state  = States.Disconnected
    parent = None
    index  = -1
    conn   = None

    def task(self):
        if   self.state == self.States.Disconnected: return
        elif self.state == self.States.WaitReady:    self.waitReady()
        elif self.state == self.States.WaitDevice:   self.waitDevice()
        elif self.state == self.States.Ready:        self.forward()

    def disconnect(self):
        self.state = self.States.Disconnected
        self.tryClose()

    def connectRelay(self, token, relayPort, relayAddr):
        data = b''
        data += token
        data += b'0' * 56
        if self.tryConnect((relayAddr, relayPort), data):
            self.setKeepAlive()
            self.state = self.States.WaitReady
            return True
        else:
            return False

    def waitReady(self):
        data = self.tryRecv(8)
        if data == b'Ready !\n':
            self.state = self.States.WaitDevice
            if self.mode == self.Modes.Client:
                self.listenDV()
        else:
            self.disconnect()

    def listenDV(self):
        connSocket, addr = self.conn.accept()
        connSocket.settimeout(0.2)
        connSocket.setblocking(False)
        # We need to upgrade connSocket from socket.socket to Connector
        self.conn = connSocket

    def waitDevice(self):
        if   self.mode == self.Modes.Portal: self.connectTo()
        elif self.mode == self.Modes.Client: self.acceptDV()

    def connectTo(self):
        deviceInfo = self.tryRecv(1024)
        l = len(deviceInfo)
        if l > 2:
            devicePort = int.from_bytes(deviceInfo[0:2], 'little')
            deviceAddr = str(deviceInfo[2:], 'utf-8')

            self.conn = DeviceConn(logDV, socket.SOCK_STREAM, 2, self.parent.port, self.parent.address)
            for i in range(3):
                if self.conn.tryConnect((deviceAddr, devicePort)):
                    self.conn.conRT = self
                    self.state = self.States.Ready
                    self.parent.conDVs[self.index] = self.conn
                    return
                else:
                    self.conn.tryClose()
            self.conn = None
        self.disconnect()

    def acceptDV(self):
        self.conn.listen()

    def forward(self):
        data = self.tryRecv(32768)
        if len(data) < 1:
            self.conn.tryClose()
            self.disconnect()
            return
        try:
            self.conn.sendall(data)
        except ConnectionAbortedError:
            self.disconnect()

class Portal:

    def __init__(self, portalID, port=0, address='0.0.0.0'):
        self.portalID = portalID
        self.port     = port
        self.address  = address
        self.conST    = None
        self.conRTs   = []
        self.conDVs   = []

    def main(self):
        if not self.conST:
            self.connectKA()
        else:
            socketList = [self.conST] + self.conRTs + self.conDVs
            socketList = filter(None, socketList)
            readable, writable, exceptional = select.select(socketList, [], [])
            for s in readable:
                if   s is self.conST: self.task()
                else:                 self.taskRTorDV(s) # s is in self.conRTs or .conDVs

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
                self.conDVs.append(None)
                break
            else:
                conRT.tryClose()

    def taskRTorDV(self, con):
        con.task()

        conRT = con if isinstance(con, RelayConnector) else con.conRT
        if conRT.state == conRT.States.Disconnected:
            self.conRTs[conRT.index] = None
            self.conDVs[conRT.index] = None

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
