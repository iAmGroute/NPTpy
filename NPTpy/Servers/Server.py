# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket
import select

from Common.Connector import Connector

log   = logging.getLogger(__name__ + '   ')
logRT = logging.getLogger(__name__ + ':RT')
# logRU = logging.getLogger(__name__ + ':RU')

class PortalConn:
    def __init__(self, portalID, addr, baseSocket):
        self.portalID    = portalID
        self.addr        = addr
        self.baseSocket  = baseSocket
        self.portalIndex = -1

    def recv(self, size):
        return self.baseSocket.recv(size)

    def sendall(self, data):
        return self.baseSocket.sendall(data)

    def tryClose(self):
        try:
            self.baseSocket.close()
        except socket.error:
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.baseSocket.fileno()

RelayManageAddr = '127.0.0.1'
RelayManagePort = 40401

class Server:

    def __init__(self, port, address='0.0.0.0'):
        self.con   = Connector(log,   socket.SOCK_STREAM, None, port, address)
        self.conRT = Connector(logRT, socket.SOCK_STREAM, None, 40402, '0.0.0.0')
        self.con.listen()
        self.conRT.connect((RelayManageAddr, RelayManagePort))
        self.portalTable   = [] # TODO: convert to pool allocator
        self.portalIndexer = {} # Dictionary (hash table)

    class Methods:
        # A method returns <(reply, close)>,
        # where <reply> is:
        #   - a bytearray with the data to send as a reply
        #   - a bytearray which is empty (b'') and then no reply is sent
        # and <close> is
        #   - True, if the connection should be closed right after sending the reply
        #   - False, if it should be kept open

        # Catch-all for all method codes which are not valid
        def InvalidMethod(self, record, message):
            return b'Invalid Mathod', True

        # Request to connect to portal
        def ConnectToPortal(self, record, message):
            otherID = message[4:8]
            log.info('    wants to connect to: x{0}'.format(otherID.hex()))
            try:
                otherIndex = self.portalIndexer[otherID]
            except KeyError:
                return b'Bad ID', True
            else:
                log.info('    found')
                self.notifyRelay(b'01234567', record.portalID, otherID) # TODO: generate token with system urandom (crypto)
                # TODO: add the following to a task queue and wait for positive reply from relay
                # before notifying the portal
                otherRecord = self.portalTable[otherIndex]
                self.notifyPortal(otherRecord, record)
                return b'realy_ip:port', True # this should be False, until we get confirm from relay & portal

    def notifyRelay(self, token, callerID, otherID):
        msg =  b'v0.1'  # 4B
        msg += b'ADD.'  # 4B
        msg += token    # 8B
        msg += callerID # 4B
        msg += otherID  # 4B
        self.conRT.sendall(msg) # 24B

    def notifyPortal(self, conn, callerRecord):
        conn.sendall(b'realy_ip:port') # TODO: also send caller's info from callerRecord

    def main(self):
        socketList = [self.con] + self.portalTable
        socketList = filter(None, socketList)
        readable, writable, exceptional = select.select(socketList, [], socketList)
        for s in readable:
            if   s is self.con: self.task()
            else:               self.process(s) # s is in self.connSockets
        for s in exceptional:
            if   s is self.con: pass
            else:               self.removeConn(s) # s is in self.connSockets

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

            record = PortalConn(portalID, addr, conn)

            # Add the record or update the existing one
            try:
                portalIndex = self.portalIndexer[portalID]
            except KeyError:
                portalIndex = len(self.portalTable)
                self.portalTable.append(record)
                self.portalIndexer[portalID] = portalIndex
            else:
                log.info('    renew existing')
                oldRecord = self.portalTable[portalIndex]
                oldRecord.conn.tryClose()
                self.portalTable[portalIndex] = record

            record.portalIndex = portalIndex

    def removeConn(self, conn):
        conn.tryClose()
        portalID = self.portalTable[conn.portalIndex].portalID
        self.portalTable[conn.portalIndex] = None
        del self.portalIndexer[portalID]

    def process(self, conn):
        try:
            record = self.portalTable[conn.portalIndex]
        except KeyError:
            # Connection is not registered, this shouldn't happen
            log.error('    NOT IN TABLE')
            self.removeConn(conn)
            return

        data = conn.recv(64)
        if len(data) != 64:
            # Bad request, drop it
            log.info('    bad request')
            self.removeConn(conn)
            return

        methodID = int.from_bytes(data[0:4], 'little')
        if methodID >= len(methodTable):
            methodID = 0 # Invalid method

        reply, close = methodTable[methodID](self, record, data)
        if reply:
            conn.sendall(reply)
        if close:
            self.removeConn(conn)


methodTable = [
    Server.Methods.InvalidMethod,
    Server.Methods.ConnectToPortal
]
