# Keep-alive handling server

import logging
import socket
import time

from Common.Connector import Connector

log  = logging.getLogger(__name__)

class KeepaliveServer:

    def __init__(self, port, address='0.0.0.0'):
        self.con = Connector(log, socket.SOCK_DGRAM, None, port, address)
        self.accountAddressTable = []
        self.accountIndexer      = {} # Dictionary (hash table)

    def task(self):
        data, addr = self.con.recvfrom(16)

        if data[0] == 0x5A: # == b'Z'
            accountID = data[4:8]
            otp       = data[8:12]

            # Received keep-alive with address update request
            log.info('    account ID: x{0} | otp: x{1}'.format(accountID.hex(), otp.hex()))

            # TODO: ensure otp is valid
            tstamp = time.time()
            # if not:
            #log.info('    OTP INVALID')
            #return

            record = (tstamp, addr)
            try:
                accountIndex = self.accountIndexer[accountID]
                self.accountAddressTable[accountIndex] = record
            except KeyError:
                accountIndex = len(self.accountAddressTable)
                self.accountAddressTable.append(record)
                self.accountIndex[accountID] = accountIndex
                # TODO: notify main server that this accountID is registered here from now on

    def tellAccountToConnect(self, accountID):
        # Throws KeyError if accountID is not found.
        accountIndex = self.accountIndexer[accountID]
        addr         = self.accountAddressTable[accountIndex]

        header = b'CONN'

        tstamp = time.time()
        # Calculate otp
        otp = b'0000'
        data = header + otp
        self.con.sendto(data, addr)

    def tellAccountToConnectTo(self, accountID, serverURL):
        # Throws KeyError if accountID is not found.
        accountIndex = self.accountIndexer[accountID]
        addr         = self.accountAddressTable[accountIndex]

        header = b'CONT'

        tstamp = time.time()
        # Calculate otp
        otp = b'0000'
        data = header + otp + bytes(serverURL, 'utf-8')
        self.con.sendto(data, addr)
