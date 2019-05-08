# Relay server

# TODO:
# use different token for A and B (?) to prevent hijacking

import logging
import socket
import select
from recordclass import recordclass

from Common.Connector import Connector

log   = logging.getLogger(__name__ + '   ')
logST = logging.getLogger(__name__ + ':ST')
# logSU = logging.getLogger(__name__ + ':SU')

class RelayConn:
    def __init__(self, baseSocket):
        self.baseSocket = baseSocket
        self.token = b''
        self.other = None

    def recv(self, size):
        return self.baseSocket.recv(size)

    def sendall(self, data):
        return self.baseSocket.sendall(data)

    def tryClose(self):
        self.other = None
        try:
            self.baseSocket.close()
        except socket.error:
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.baseSocket.fileno()

MapRecord = recordclass('MapRecord', ['indexA', 'indexB'])

class Relay:

    def __init__(self, port, address='0.0.0.0'):
        self.con   = Connector(log,   socket.SOCK_STREAM, None, port, address) # for portals/clients
        self.conST = Connector(logST, socket.SOCK_STREAM, None, 40401, '0.0.0.0') # for server
        self.con.listen()
        self.conST.listen()
        self.connST = None
        self.connSockets = [] # TODO: convert to pool allocator / slot map
        self.tokenMap    = {} # Dictionary (hash table)

    def main(self):
        socketList = [self.con, self.conST, self.connST] + self.connSockets
        socketList = filter(None, socketList)
        readable, writable, exceptional = select.select(socketList, [], socketList)
        for s in readable:
            if   s is self.con:    self.task()
            elif s is self.conST:  self.taskManageAccept()
            elif s is self.connST: self.taskManage()
            else:                  self.process(s) # s is in self.connSockets
        for s in exceptional:
            if   s is self.con:    pass # TODO: Handle to prevent inf loop
            elif s is self.conST:  pass # same
            elif s is self.connST: self.removeManage()
            else:                  self.removeConn(s) # s is in self.connSockets

    def taskManageAccept(self):
        conn, addr = self.conST.accept()
        conn.setblocking(False)
        if self.connST:
            self.removeManage()
        self.connST = conn

    def removeManage(self):
        try:
            self.connST.close()
        except socket.error:
            pass
        self.connST = None

    def taskManage(self):
        try:
            data = self.connST.recv(24)
        except socket.error:
            pass
        else:
            if len(data) == 24:
                magic    = data[0:4]
                verb     = data[4:8]
                token    = data[8:16]
                callerID = data[16:20]
                otherID  = data[20:24]
                logST.info('New command:')
                logST.info('    verb:     {0}   | token:   x{1}'.format(verb, token.hex()))
                logST.info('    callerID: x{0} | otherID: x{1}'.format(callerID.hex(), otherID.hex()))

                # We don't store the IDs, although we should, for validation/security check
                if verb == b'ADD.':
                    self.removeByToken(token)
                    self.tokenMap[token] = MapRecord(-1, -1)
                elif verb == b'DEL.':
                    self.removeByToken(token)

                self.connST.sendall(b'OK')

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

                    newSocket       = RelayConn(conn)
                    newSocket.token = token
                    rec.indexA = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    log.info('    indexA: {0:3d}'.format(rec.indexA))

                elif rec.indexB == -1:
                    # Second one to connect
                    other = self.connSockets[rec.indexA]

                    newSocket       = RelayConn(conn)
                    newSocket.token = token
                    newSocket.other = other
                    rec.indexB = len(self.connSockets)
                    self.connSockets.append(newSocket)

                    # we can now forward between the 2
                    other.other = newSocket

                    newSocket.sendall(b'Ready !\n')
                    other.sendall(b'Ready !\n')

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
        if conn.other:
            conn.other.tryClose()
        conn.tryClose()
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
        # TODO: avoid reading data if other is not connected,
        # but check to see if this one has disconnected
        data = conn.recv(2048)
        if len(data) < 1:
            # Connection closed (?), remove both
            self.removeConn(conn)

        if conn.other:
            conn.other.sendall(data)
