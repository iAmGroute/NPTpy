# Unified server for managing portals (KA) & connections to relay server.

import logging
import socket
import select
import time

from Common.SlotList  import SlotList
from Common.Connector import Connector

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

        self.callbacksRT = SlotList(10)

        self.relayInfoMessage = relayPort.to_bytes(2, 'little') + bytes(relayAddr, 'utf-8')

        self.con = Connector(log,  Connector.new(socket.SOCK_STREAM, None, port, address))
        self.con.secureServer(certFilename='server.cer', keyFilename='server.key')
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
        def InvalidMethod(self, portal, message):
            return b'Invalid Mathod', True


        # Request to connect to portal
        def ConnectToPortal(self, portal, message):
            otherID = message[4:8]
            log.info('    wants to connect to: x{0}'.format(otherID.hex().upper()))
            try:
                otherIndex = self.portalIndexer[otherID]
            except KeyError:
                log.info('    not in table')
                return b'Bad ID', False
            else:
                log.info('    found')
                other = self.portalTable[otherIndex]
                ref = self.callbacksRT.append((self.handleRelayReady, (portal, other)))
                self.notifyRelay(ref, portal.portalID, otherID)
                return None, False


    def handleRelayReady(self, params, data):
        if len(data) < 8:
            return False
        token = data[0:8]
        portalA, portalB = params
        self.notifyPortal(portalA, portalB, token)
        self.notifyPortal(portalB, portalA, token)
        return True


    def notifyRelay(self, ref, callerID, otherID):
        msg =  ref.to_bytes(8, 'little') # 8B
        msg += b'v0.1'                   # 4B
        msg += b'ADD.'                   # 4B
        msg += callerID                  # 4B
        msg += otherID                   # 4B
        self.conRT.sendall(msg)          # 24B


    def notifyPortal(self, portal, caller, token):
        # TODO: also send caller's info
        msg =  b'v0.1'               # 4B
        msg += caller.portalID       # 4B
        msg += token                 # 8B
        msg += self.relayInfoMessage # 2B + var
        portal.sendall(msg)          # 18B + var


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
        packet = self.conRT.tryRecv(1024)
        if packet is None:
            return
        if len(packet) < 8:
            self.conRT = None
        ref  = int.from_bytes(packet[0:8], 'little')
        data = packet[8:]
        callback = self.callbacksRT[ref]
        if callback:
            del self.callbacksRT[ref]
            method, params = callback
            ok = method(params, data)
            if not ok:
                self.conRT = None


    def task(self):
        connSocket, addr = self.con.tryAccept()
        if not connSocket:
            return
        connSocket.settimeout(0.2)
        try:
            data = connSocket.recv(64)
            connSocket.settimeout(0)
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
            portal = self.portalTable[conn.portalIndex]
        except KeyError:
            # Connection is not registered, this shouldn't happen
            log.error('    NOT IN TABLE')
            self.removeConn(conn)
            return

        data = conn.tryRecv(64)
        if data is None:
            return
        if len(data) != 64:
            # Remove the connection
            log.info('    disconnect' if len(data) == 0 else '    bad request')
            self.removeConn(conn)
            return

        methodID = int.from_bytes(data[0:4], 'little')
        if methodID >= len(methodTable):
            methodID = 0 # Invalid method

        reply, close = methodTable[methodID](self, portal, data)
        if reply:
            if not conn.trySendall(reply):
                close = True
        if close:
            self.removeConn(conn)


methodTable = [
    Server.Methods.InvalidMethod,
    Server.Methods.ConnectToPortal
]
