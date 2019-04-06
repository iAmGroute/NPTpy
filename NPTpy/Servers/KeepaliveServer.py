# Keep-alive handling server

import logging
import socket
import time

from Common.Connector import Connector

log  = logging.getLogger(__name__)

class KeepaliveServer:

    def __init__(self, port, address='0.0.0.0'):
        self.con = Connector(log, socket.SOCK_DGRAM, None, port, address)
        self.portalAddressTable = []
        self.portalIndexer      = {} # Dictionary (hash table)

    def task(self):
        data, addr = self.con.recvfrom(16)

        # Register as primary server
        # TODO: add another symbol for unregister
        # TODO: add 2 more symbols for backup server
        if data[0] == 0x5A: # == b'Z'
            portalID = data[4:8]
            otp      = data[8:12]

            # Received keep-alive with address update request
            log.info('    portal ID: x{0} | otp: x{1}'.format(portalID.hex(), otp.hex()))

            # TODO: ensure otp is valid
            tstamp = time.time()
            # if not:
            #log.info('    OTP INVALID')
            #return

            record = (tstamp, addr)
            try:
                portalIndex = self.portalIndexer[portalID]
                self.portalAddressTable[portalIndex] = record
            except KeyError:
                portalIndex = len(self.portalAddressTable)
                self.portalAddressTable.append(record)
                self.portalIndex[portalID] = portalIndex
                # TODO: notify main server that this portalID is registered here from now on

            # Reply with external IP and port
            # this also works as a keepalive reply.
            data[4:8]  = addr[0].to_bytes(4, 'little')
            data[8:12] = addr[1].to_bytes(4, 'little')
            self.con.sendto(data, addr)

    def tellPortalToConnect(self, portalID):
        # Throws KeyError if portalID is not found.
        portalIndex = self.portalIndexer[portalID]
        addr        = self.portalAddressTable[portalIndex]

        header = b'CONN'

        tstamp = time.time()
        # Calculate otp
        otp = b'0000'
        data = header + otp
        self.con.sendto(data, addr)

    def tellPortalToConnectTo(self, portalID, serverURL):
        # Throws KeyError if portalID is not found.
        portalIndex = self.portalIndexer[portalID]
        addr        = self.portalAddressTable[portalIndex]

        header = b'CONT'

        tstamp = time.time()
        # Calculate otp
        otp = b'0000'
        data = header + otp + bytes(serverURL, 'utf-8')
        self.con.sendto(data, addr)
