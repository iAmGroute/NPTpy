# Relay server

# TODO:
# use different token for A and B (?) to prevent hijacking

import logging
import socket

from Common.Connector import Connector

log   = logging.getLogger(__name__)
logPT = logging.getLogger(__name__ + ':PT')
# logPU = logging.getLogger(__name__ + ':PU')

class ConnSocket(socket.socket):
    token = b''
    other = None

    def tryClose(self):
        try:
            self.close()
        except socket.error:
            return False
        return True

MapRecord = namedtuple('MapRecord', ['indexA', 'indexB'])

class Server:

    def __init__(self, port, address='0.0.0.0'):
        self.con   = Connector(log,   socket.SOCK_STREAM, None, port, address)
        self.conPT = Connector(logPT, socket.SOCK_STREAM, None, port, address)
        self.con.listen()
        self.conPT.listen()
        self.connSockets = [] # TODO: convert to pool allocator
        self.tokenMap    = {} # Dictionary (hash table)

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

                    newSocket       = ConnSocket(conn)
                    newSocket.token = token
                    rec.indexA = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    log.info('    indexA: {3d}'.format(rec.indexA))

                elif rec.indexB == -1:
                    # Second one to connect

                    newSocket       = ConnSocket(conn)
                    newSocket.token = token
                    newSocket.other = self.connSockets[rec.indexA]
                    rec.indexB = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    # we can now forward between the 2
                    self.connSockets[rec.indexA].other = newSocket

                    log.info('    indexA: {3d}, indexB: {3d}'.format(rec.indexA, rec.indexB))

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

    def proccess(self, conn):
        data = conn.recv(2048)
        if len(data) < 1:
            # Connection closed (?), remove both
            self.removeConn(conn)

        if conn.other:
            conn.other.sendall(reply)
