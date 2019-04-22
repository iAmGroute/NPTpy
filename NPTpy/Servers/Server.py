# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket

from Common.Connector import Connector

log = logging.getLogger(__name__)

class Methods:
    @staticmethod
    def InvalidMethod(message):
        return b'\x00'
    @staticmethod
    def Connect(message):
        return b'\x00'

methodTable = [
    Methods.InvalidMethod,
    Methods.Connect
]

PortalRecord = namedtuple('PortalRecord', ['portalID', 'addr', 'conn'])

class Server:

    def __init__(self, port, address='0.0.0.0'):
        self.con = Connector(log, socket.SOCK_STREAM, None, port, address)
        self.con.listen()
        self.portalTable   = []
        self.portalIndexer = {} # Dictionary (hash table)

    def task(self):
        conn, addr = self.con.accept()
        conn.settimeout(0.2)
        try:
            data = conn.recv(64)
        except socket.error:
            pass
        else:
            portalID = data[0:4]

            log.info('    with portalID: x{0}'.format(portalID.hex()))

            # TODO: authenticate
            conn.sendall(b'\x00')

            record = PortalRecord(portalID, addr, conn)
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
                del oldRecord.conn
                self.portalTable[portalIndex] = record

    def removeConn(self, conn):
        pass

    def proccess(self, conn):
        ##if conn available >= 64:
            data = conn.recv(64)
            methodID = int.from_bytes(data[0:4], 'little')
            if methodID >= len(methodTable):
                methodID = 0
            reply = methodTable[methodID](data)
            if reply:
                conn.sendall(reply)
            else:
                conn.close()
                self.removeConn(conn)
