# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket
import select
import time
import os      # for os.urandom

from Common.Connector       import Connector
from Common.SecureConnector import SecureServerConnector

log  = logging.getLogger(__name__ + '  ')
logP = logging.getLogger(__name__ + ':P')
logR = logging.getLogger(__name__ + ':R')

class PortalConn(Connector):
    def __init__(self, portalID, addr, mySocket):
        Connector.__init__(self, logP, mySocket)
        self.portalID    = portalID
        self.addr        = addr
        self.portalIndex = -1


class Server:


    def __init__(self, port, address, internalPort, internalAddr, relayPort, relayAddr, relayInternalPort, relayInternalAddr):

        self.internalPort      = internalPort
        self.internalAddr      = internalAddr
        self.relayInternalPort = relayInternalPort
        self.relayInternalAddr = relayInternalAddr
        self.conRT = None

        self.relayInfoMessage = relayPort.to_bytes(2, 'little') + bytes(relayAddr, 'utf-8')

        self.con = SecureServerConnector(log,  Connector.new(socket.SOCK_STREAM, None, port, address))
        self.con.secure(certFilename='server.cer', keyFilename='server.key')
        self.con.listen()

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
            log.info('    wants to connect to: x{0}'.format(otherID.hex().upper()))
            try:
                otherIndex = self.portalIndexer[otherID]
            except KeyError:
                log.info('    not in table')
                return b'Bad ID', False
            else:
                log.info('    found')
                token = os.urandom(8)
                self.notifyRelay(token, record.portalID, otherID)
                # TODO: add the following to a task queue and wait for positive reply from relay
                # before notifying the portal
                otherConn = self.portalTable[otherIndex]
                self.notifyPortal(otherConn, record, token)
                msg = token + self.relayInfoMessage
                return msg, False


    def notifyRelay(self, token, callerID, otherID):
        msg =  b'v0.1'  # 4B
        msg += b'ADD.'  # 4B
        msg += token    # 8B
        msg += callerID # 4B
        msg += otherID  # 4B
        self.conRT.sendall(msg) # 24B


    def notifyPortal(self, portalConn, callerRecord, token):
        # TODO: also send caller's info from callerRecord
        msg =  b'v0.1'               # 4B
        msg += callerRecord.portalID # 4B
        msg += token                 # 8B
        msg += self.relayInfoMessage # 2B + var
        portalConn.sendall(msg)      # 18B + var


    def main(self):
        if not self.conRT:
            self.connectRT()
        else:
            socketList = [self.con, self.conRT] + self.portalTable
            socketList = filter(None, socketList)
            readable, writable, exceptional = select.select(socketList, [], [])
            for s in readable:
                if   s is self.con:   self.task()
                elif s is self.conRT: self.taskRelay()
                else:                 self.process(s) # s is in self.portalTable


    def connectRT(self):
        self.conRT = Connector(logR, Connector.new(socket.SOCK_STREAM, 2, self.internalPort, self.internalAddr))
        if not self.conRT.tryConnect((self.relayInternalAddr, self.relayInternalPort)):
            self.conRT = None
            time.sleep(10)
            return
        self.conRT.setKeepAlive()


    def taskRelay(self):
        data = self.conRT.tryRecv(1024)
        if len(data) < 1:
            self.conRT = None


    def task(self):
        connSocket, addr = self.con.tryAccept()
        if not connSocket:
            return
        connSocket.settimeout(0.2)
        try:
            data = connSocket.recv(64)
            connSocket.setblocking(False)
        except OSError:
            log.info('    dropped')
        else:
            if len(data) != 64:
                connSocket.close()
                return

            portalID = data[0:4]

            log.info('    with portalID: x{0}'.format(portalID.hex().upper()))

            # TODO: authenticate
            # connSocket.sendall(b'\x00')

            conn = PortalConn(portalID, addr, connSocket)

            # Add the conn or update the existing one
            try:
                portalIndex = self.portalIndexer[portalID]
            except KeyError:
                portalIndex = len(self.portalTable)
                self.portalTable.append(conn)
                self.portalIndexer[portalID] = portalIndex
            else:
                log.info('    renew existing')
                oldConn = self.portalTable[portalIndex]
                oldConn.tryClose()
                self.portalTable[portalIndex] = conn

            conn.portalIndex = portalIndex


    def removeConn(self, conn):
        conn.tryClose()
        portalID = self.portalTable[conn.portalIndex].portalID
        self.portalTable[conn.portalIndex] = None
        del self.portalIndexer[portalID]


    def process(self, conn):
        log.info('Portal: x{0}'.format(conn.portalID.hex().upper()))
        try:
            record = self.portalTable[conn.portalIndex]
        except KeyError:
            # Connection is not registered, this shouldn't happen
            log.error('    NOT IN TABLE')
            self.removeConn(conn)
            return

        data = conn.tryRecv(64)
        if len(data) != 64:
            # Remove the connection
            log.info('    disconnect' if len(data) == 0 else '    bad request')
            self.removeConn(conn)
            return

        methodID = int.from_bytes(data[0:4], 'little')
        if methodID >= len(methodTable):
            methodID = 0 # Invalid method

        reply, close = methodTable[methodID](self, record, data)
        if reply:
            if not conn.trySendall(reply):
                close = True
        if close:
            self.removeConn(conn)


methodTable = [
    Server.Methods.InvalidMethod,
    Server.Methods.ConnectToPortal
]
