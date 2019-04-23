# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class ConnSocket(socket.socket):
    portalIndex = -1

class Methods:
    # A method returns <(reply, close)>,
    # where <reply> is:
    #   - a bytearray with the data to send as a reply
    #   - a bytearray which is empty (b'') and then no reply is sent
    # and <close> is
    #   - True, if the connection should be closed right after sending the reply
    #   - False, if it should be kept open
    @staticmethod
    def InvalidMethod(message):
        return b'\x00', True
    @staticmethod
    def Connect(message):
        return b'', False

methodTable = [
    Methods.InvalidMethod,
    Methods.Connect
]

PortalRecord = namedtuple('PortalRecord', ['portalID', 'addr', 'conn'])

class Server:

    def __init__(self, port, address='0.0.0.0'):
        self.con = Connector(log, socket.SOCK_STREAM, None, port, address)
        self.con.listen()
        self.portalTable   = [] # TODO: convert to pool allocator
        self.portalIndexer = {} # Dictionary (hash table)

    def task(self):
        conn, addr = self.con.accept()
        conn.setblocking(False)
        try:
            data = conn.recv(64)
        except socket.error:
            pass
        else:
            if len(data) != 64:
                conn.close()
                return

            portalID = data[0:4]

            log.info('    with portalID: x{0}'.format(portalID.hex()))

            # TODO: authenticate
            conn.sendall(b'\x00')

            record = PortalRecord(portalID, addr, ConnSocket(conn))

            try:
                portalIndex = self.portalIndexer[portalID]
            except KeyError:
                portalIndex = len(self.portalTable)
                self.portalTable.append(record)
                self.portalIndexer[portalID] = portalIndex
            else:
                log.info('    renew existing')
                oldRecord = self.portalTable[portalIndex]
                oldRecord.conn.close()
                self.portalTable[portalIndex] = record

            record.conn.portalIndex = portalIndex

    def removeConn(self, conn):
        try:
            conn.close()
        except socket.error:
            pass
        portalID = self.portalTable[conn.portalIndex].portalID
        self.portalTable[conn.portalIndex] = None
        del self.portalIndexer[portalID]

    def proccess(self, conn):
        data = conn.recv(64)
        if len(data) != 64:
            # Bad request, drop it
            self.removeConn(conn)

        methodID = int.from_bytes(data[0:4], 'little')
        if methodID >= len(methodTable):
            methodID = 0 # Invalid method

        reply, close = methodTable[methodID](data)
        if reply:
            conn.sendall(reply)
        if close:
            self.removeConn(conn)
