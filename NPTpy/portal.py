
import logging
import socket
import time

from Common.Connector import Connector

log  = logging.getLogger(__name__)

SERVER      = 'groute1.westeurope.cloudapp.azure.com'
SERVER_PORT = 7817

class Portal:

    def __init__(self, portalID, port, address='0.0.0.0'):
        self.con = Connector(log, socket.SOCK_DGRAM, None, port, address)
        self.portalID = portalID

    def keepaliveTask(self, serverEP, primary=True):
        data = b'0000' + portalID.to_bytes(4, 'little') + b'0000'
        code = 0x5A if primary else 0x5B # backup
        i = 0
        while True:
            # Register message every 4 messages
            # the other 3 are ignored by the server,
            # but keep the NAT happy.
            data[0] = code if (i % 4) == 0 else 0x00
            # TODO: grenerate OTP
            #data[8:12] = --- new OTP ---
            # TODO: add primary server's GUID/url if primary == False
            self.con.sendto(data, serverEP)
            time.sleep(4)

    def listen(self):
        data, addr = self.con.recvfrom(256)
        header = data[0:4]
        otp    = data[4:8]

        # TODO: verify otp

        if header == b'CONN':
            self.connect()
        elif header == b'CONT':
            serverURL = str(data[8:], 'utf-8')
            self.connect(serverURL)

        # TODO: add dead timer countdown for server
        # reset the countdown

    def connect(self, serverURL=None):
