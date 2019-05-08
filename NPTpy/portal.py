
import logging
import socket
import time

from Common.Connector import Connector

log   = logging.getLogger(__name__ + '   ')
logST = logging.getLogger(__name__ + ':ST')
logRT = logging.getLogger(__name__ + ':RT')

ServerAddr = '127.0.0.1'
ServerPort = 4020

def echo(conn):
    while True:
        data = conn.recv(1024)
        if len(data) < 1:
            return
        conn.sendall(data)

class Portal:

    def __init__(self, portalID, port=0, address='0.0.0.0'):
        self.portalID = portalID
        self.port     = port
        self.address  = address
        # TODO: change timeout from None to something else (e.g. 2),
        # once the rest is implemented with select,
        # same thing at the conRT down below
        self.conST = Connector(log, socket.SOCK_STREAM, None, port, address)
        self.connected = False

    def tryConnect(self, con, endpoint, data):
        try:
            con.connect(endpoint)
            con.sendall(data)
            con.setKeepAlive()
        except socket.error as e:
            print(e)
            con.tryClose()
            return False
        return True

    def connectKA(self):
        data = b''
        data += self.portalID
        data += b'0' * 60
        self.connected = self.tryConnect(self.conST, (ServerAddr, ServerPort), data)

    def connectRelay(self, conRT, token, relayPort, relayAddr):
        data = b''
        data += token
        data += b'0' * 56
        return self.tryConnect(conRT, (relayAddr, relayPort), data)

    def task(self):
        relayInfo = self.conST.recv(1024)
        if len(relayInfo) < 1:
            self.connected = False
            return
        token     = relayInfo[0:8]
        relayPort = int.from_bytes(relayInfo[8:10], 'little')
        relayAddr = str(relayInfo[10:], 'utf-8')
        with Connector(logRT, socket.SOCK_STREAM, None, self.port, self.address) as conRT:
            if self.connectRelay(conRT, token, relayPort, relayAddr):
                data = conRT.recv(8)
                if data == b'Ready !\n':
                    echo(conRT)

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
