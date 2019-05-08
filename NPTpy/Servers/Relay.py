# Relay server

# TODO:
# use different token for A and B (?) to prevent hijacking

import logging
import socket
from recordclass import recordclass

from Common.Connector import Connector

log   = logging.getLogger(__name__ + '   ')
logST = logging.getLogger(__name__ + ':ST')
# logSU = logging.getLogger(__name__ + ':SU')

class RelayConnSocket:
    def __init__(self, baseSocket):
        self.baseSocket = baseSocket
        self.token = b''
        self.other = None

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

MapRecord = recordclass('MapRecord', ['indexA', 'indexB'])

class Relay:

    def __init__(self, port, address='0.0.0.0'):
        self.con   = Connector(log,   socket.SOCK_STREAM, None, port, address) # for portals/clients
        self.conST = Connector(logST, socket.SOCK_STREAM, None, 40401, '0.0.0.0') # for server
        self.con.listen()
        self.conST.listen()
        self.connSockets = [] # TODO: convert to pool allocator
        self.tokenMap    = {} # Dictionary (hash table)

    def taskManage(self):
        conn, addr = self.conST.accept()
        # while conn:
        with conn:
            try:
                data = conn.recv(20)
            except socket.error:
                pass
            else:
                if len(data) == 20:
                    verb     = data[0:4]
                    callerID = data[4:8]
                    otherID  = data[8:12]
                    token    = data[12:20]
                    log.info('    new command:')
                    log.info('    verb: {0} callerID: {1} otherID: {2}'.format(verb, callerID.hex(), otherID.hex()))
                    log.info('    token: x{0}'.format(token.hex()))

                    # We don't store the IDs, although we should, for validation/security check
                    if verb == b'ADD.':
                        self.removeByToken(token)
                        self.tokenMap[token] = MapRecord(-1, -1)
                    elif verb == b'DEL.':
                        self.removeByToken(token)

                    conn.sendall(b'OK')

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

            token = data[0:8]

            log.info('    with token: x{0}'.format(token.hex()))

            try:
                rec = self.tokenMap[token]
            except KeyError:
                log.info('    INVALID')
                conn.close()
                return
            else:
                if rec.indexA == -1:
                    # First one to connect

                    newSocket       = RelayConnSocket(conn)
                    newSocket.token = token
                    rec.indexA = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    log.info('    indexA: {0:3d}'.format(rec.indexA))

                elif rec.indexB == -1:
                    # Second one to connect

                    newSocket       = RelayConnSocket(conn)
                    newSocket.token = token
                    newSocket.other = self.connSockets[rec.indexA]
                    rec.indexB = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    # we can now forward between the 2
                    self.connSockets[rec.indexA].other = newSocket

                    log.info('    indexA: {0:3d}, indexB: {1:3d}'.format(rec.indexA, rec.indexB))

                else:
                    log.info('    REUSE')
                    conn.close()
                    return

    def removeIndex(self, index):
        try:
            self.connSockets[index] = None
        except IndexError:
            return False
        return True

    def closeByIndex(self, index):
        try:
            conn = self.connSockets[index]
            self.connSockets[index] = None
        except IndexError:
            conn = None

        return conn.tryClose() if conn else False

    def removeConn(self, conn):
        conn.tryClose()
        if conn.other:
            conn.other.tryClose()
        try:
            rec = self.tokenMap[conn.token]
        except KeyError as e:
            log.exception(e)
        else:
            self.removeIndex(rec.indexA)
            self.removeIndex(rec.indexB)
            del self.tokenMap[conn.token]

    def removeByToken(self, token):
        try:
            rec = self.tokenMap[token]
        except KeyError:
            pass
        else:
            self.closeByIndex(rec.indexA)
            self.closeByIndex(rec.indexB)
            del self.tokenMap[token]

    def process(self, conn):
        data = conn.recv(2048)
        if len(data) < 1:
            # Connection closed (?), remove both
            self.removeConn(conn)

        if conn.other:
            conn.other.sendall(data)
