# Relay server

# TODO: use different token for A and B (?) to prevent hijacking
# TODO: implement a timeout for the active tokens which do not have both ends connected

import logging
import socket
import select

from Common.SlotList  import SlotList
from Common.Connector import Connector

log  = logging.getLogger(__name__ + '  ')
logP = logging.getLogger(__name__ + ':P')
logS = logging.getLogger(__name__ + ':S')

class RelayConn(Connector):

    def __init__(self, mySocket):
        Connector.__init__(self, logP, mySocket)
        self.token = b''
        self.other = None

    def tryClose(self):
        self.other = None
        super().tryClose()


class MapRecord:

    def __init__(self, indexA, indexB):
        self.indexA = indexA
        self.indexB = indexB

    def __repr__(self):
        return '(indexA: {0}, indexB: {1})'.format(self.indexA, self.indexB)


class Relay:

    def __init__(self, port, address, internalPort, internalAddr):
        self.con   = Connector(log,  Connector.new(socket.SOCK_STREAM, None,         port,      address)) # for portals/clients
        self.con.listen()
        self.conST = Connector(logS, Connector.new(socket.SOCK_STREAM, None, internalPort, internalAddr)) # for server
        self.conST.listen()
        self.connST = None
        self.connSockets = SlotList(16)
        self.tokenMap    = {} # Dictionary (hash table)


    def main(self):
        socketList = [self.con, self.conST, self.connST]
        socketList.extend(self.connSockets)
        socketList = filter(None, socketList)
        readable, writable, exceptional = select.select(socketList, [], [])
        for s in readable:
            if   s is self.con:    self.task()
            elif s is self.conST:  self.taskManageAccept()
            elif s is self.connST: self.taskManage()
            else:                  self.process(s) # s is in self.connSockets


    def taskManageAccept(self):
        connSocket, addr = self.conST.accept()
        # connSocket.setblocking(False)
        if self.connST:
            self.removeManage()
        self.connST = Connector(logS, connSocket)


    def removeManage(self):
        self.connST.tryClose()
        self.connST = None


    def taskManage(self):

        data = self.connST.tryRecv(24)
        if len(data) != 24:
            self.removeManage()
            return

        magic    = data[0:4]
        if magic != b'v0.1':
            return
        verb     = data[4:8]
        token    = data[8:16]
        callerID = data[16:20]
        otherID  = data[20:24]
        logS.info('New command:')
        logS.info('    verb:     {0}   | token:   x{1}'.format(verb, token.hex().upper()))
        logS.info('    callerID: x{0} | otherID: x{1}'.format(callerID.hex().upper(), otherID.hex().upper()))

        # We don't store the IDs, although we should, for validation/security check
        if verb == b'ADD.':
            self.removeByToken(token)
            self.tokenMap[token] = MapRecord(-1, -1)
        elif verb == b'DEL.':
            self.removeByToken(token)

        self.connST.sendall(b'OK')


    def task(self):

        connSocket, addr = self.con.accept()
        # connSocket.settimeout(0.2)

        conn = RelayConn(connSocket)

        data = conn.tryRecv(64)
        # TODO: states + select instead of non-block,
        # since sendall() must be able block
        # conn.socket.setblocking(False)
        if len(data) != 64:
            conn.tryClose()
            return

        conn.token = data[0:8]
        logP.info('    with token: x{0}'.format(conn.token.hex().upper()))

        try:
            rec = self.tokenMap[conn.token]

        except KeyError:
            logP.info('    INVALID')
            conn.sendall(b'Bad T !\n')
            conn.tryClose()
            return

        else:

            if rec.indexA == -1:
                # First one to connect

                rec.indexA = self.connSockets.append(conn)
                if rec.indexA < 0:
                    logP.warn('    registration failed, connSockets is full !')
                    return

                logP.info('    indexA: {0:3d}'.format(rec.indexA))

            elif rec.indexB == -1:
                # Second one to connect

                other = self.connSockets[rec.indexA]

                conn.other = other
                rec.indexB = self.connSockets.append(conn)
                if rec.indexB < 0:
                    logP.warn('    registration failed, connSockets is full !')
                    return

                # we can now forward between the 2
                other.other = conn

                conn.sendall(b'Ready !\n')
                other.sendall(b'Ready !\n')

                logP.info('    indexA: {0:3d}, indexB: {1:3d}'.format(rec.indexA, rec.indexB))

            else:
                logP.info('    REUSE')
                conn.sendall(b'Bad T !\n')
                conn.tryClose()
                return


    def removeIndex(self, index):
        try:
            del self.connSockets[index]
        except IndexError:
            return False
        return True


    def closeByIndex(self, index):
        try:
            conn = self.connSockets[index]
            del self.connSockets[index]
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
        # Note: we need to drop the incoming data to prevent this conn from being picked again on select().
        #       So, we can't wait for the other to connect and instead we disconnect both endpoints.
        data = conn.tryRecv(32768)
        if len(data) < 1 or not conn.other:
            # Connection closed or other is not connected, remove both
            self.removeConn(conn)
            return
        try:
            conn.other.sendall(data)
        except OSError:
            log.error('OSError')
            # Connection closed (?), remove both
            self.removeConn(conn)

