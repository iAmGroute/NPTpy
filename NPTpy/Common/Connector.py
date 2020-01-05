
import socket
import ssl
from enum import Enum

import Globals

from .this_OS       import OS, this_OS
from .Connector_log import LogClass, Etypes


def newSocket(socketType=socket.SOCK_STREAM, timeout=0, port=0, address='0.0.0.0', proto=0):
    af = socket.AF_INET if address.count('.') == 3 else socket.AF_INET6
    s  = socket.socket(af, socketType, proto)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.settimeout(timeout)
    s.bind((address, port))
    return s

def _newSocket(args):
    if type(args) is tuple: return newSocket(*args)
    else:                   return newSocket(**args)


class Connector:

    def __init__(self, fromSocket=None, new=None, fromConnector=None):
        if fromConnector:
            self.log       = fromConnector.log.upgrade(LogClass)
            self.listening = fromConnector.listening
            self.incoming  = fromConnector.incoming
            self.socket    = fromConnector.socket
        else:
            self.log       = Globals.logger.new(LogClass)
            self.listening = False
            self.incoming  = True
            self.log(Etypes.Initing, fromSocket, new)
            self.socket    = fromSocket if fromSocket else _newSocket(new)
            s = self.socket
            if s.type == socket.SOCK_STREAM:
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                # s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NOTSENT_LOWAT, 16 * 1024)
            sname         = s.getsockname()
            address, port = sname[0], sname[1]
            self.log(Etypes.Inited, address, port)

    def reprEndpoints(self):
        lname  = self.socket.getsockname()
        la, lp = lname[0], lname[1]
        res    = f'[{la}]:{lp}'
        if self.listening:
            res += '\'L'
        try:
            rname = self.socket.getpeername()
        except OSError:
            rname = None
        if rname:
            ra, rp = rname[0], rname[1]
            res += '<-' if self.incoming else '->'
            res += f'[{ra}]:{rp}'
        return res

    def __repr__(self):
        return f'<Connector {self.reprEndpoints()}>'

    def __enter__(self):
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        self.tryClose()

    def close(self):
        self.log(Etypes.Closing)
        self.socket.close()
        self.log(Etypes.Closed)

    def tryClose(self):
        try:
            self.close()
        except OSError as e:
            self.log(Etypes.Error, e)
            return False
        return True

    def shutdown(self, read, write):
        self.log(Etypes.Shutdown, read, write)
        if   read and write: self.socket.shutdown(socket.SHUT_RDWR)
        elif read:           self.socket.shutdown(socket.SHUT_RD)
        elif write:          self.socket.shutdown(socket.SHUT_WR)
        self.log(Etypes.ShutdownDone)

    def tryShutdown(self, read, write):
        try:
            self.shutdown(read, write)
        except OSError as e:
            self.log(Etypes.Error, e)
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.socket.fileno()

    # Mainly UDP

    def sendto(self, data, addr):
        self.log(Etypes.SendingTo, len(data), *addr)
        self.log(Etypes.Content, data)
        sentSize = self.socket.sendto(data, addr)
        self.log(Etypes.Sent, sentSize)
        return sentSize

    def recvfrom(self, bufferSize):
        self.log(Etypes.Receiving, bufferSize)
        data, addr = self.socket.recvfrom(bufferSize)
        self.log(Etypes.ReceivedFrom, len(data), *addr)
        self.log(Etypes.Content, data)
        return data, addr

    # Mainly TCP

    def listen(self):
        self.log(Etypes.Listen)
        self.socket.listen()
        self.listening = True

    def accept(self):
        self.log(Etypes.Accepting)
        conn, addr = self.socket.accept()
        conn.settimeout(self.socket.gettimeout())
        self.log(Etypes.Accepted, *addr)
        return conn, addr

    def decline(self):
        self.log(Etypes.Declining)
        conn, addr = self.socket.accept()
        del conn
        self.log(Etypes.Declined, *addr)
        # try:
        #     conn.settimeout(0)
        #     conn.close()
        # except OSError:
        #     pass
        return addr

    def tryAccept(self):
        try:
            conn, addr = self.accept()
        except OSError as e:
            conn, addr = None, None
            self.log(Etypes.Error, e)
        return conn, addr

    def tryDecline(self):
        try:
            addr = self.decline()
        except OSError as e:
            addr = None
            self.log(Etypes.Error, e)
        return addr

    def connect(self, endpoint):
        self.log(Etypes.Connecting, *endpoint)
        self.incoming = False
        self.socket.connect(endpoint)
        self.log(Etypes.Connected)

    def tryConnect(self, endpoint):
        try:
            self.connect(endpoint)
            return True
        except OSError as e:
            self.log(Etypes.Error, e)
            return False

    def sendall(self, data):
        self.log(Etypes.Sending, len(data))
        self.log(Etypes.Content, data)
        self.socket.sendall(data)
        self.log(Etypes.Sent, len(data))

    def trySendall(self, data):
        try:
            self.sendall(data)
            return True
        except OSError as e:
            self.log(Etypes.Error, e)
            return False

    def recv(self, bufferSize):
        self.log(Etypes.Receiving, bufferSize)
        data = self.socket.recv(bufferSize)
        self.log(Etypes.Received, len(data))
        self.log(Etypes.Content, data)
        return data

    def tryRecv(self, bufferSize):
        try:
            return self.recv(bufferSize)
        except OSError as e:
            if e.errno == 11 or isinstance(e, ssl.SSLError) and e.errno == ssl.SSL_ERROR_WANT_READ:
                # Partial or empty ssl record received and saved internally.
                # No data is available but the connection is still OK.
                return None
            else:
                self.log(Etypes.Error, e)
                return b''

    def setKeepAlive(self, idleTimer=10, interval=10, probeCount=10):
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if   this_OS == OS.linux:
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,  idleTimer)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval)
                self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT,   probeCount)
            elif this_OS == OS.mac:
                self.socket.setsockopt(socket.IPPROTO_TCP, 0x10, interval)
            elif this_OS == OS.windows:
                self.socket.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 1000 * idleTimer, 1000 * interval))
        except OSError:
            return False
        return True

    def secureClient(self, serverHostname, caFilename=None, caDirpath=None, caData=None):
        ctx         = ssl.create_default_context(cafile=caFilename, capath=caDirpath, cadata=caData)
        self.socket = ctx.wrap_socket(self.socket, server_hostname=serverHostname, do_handshake_on_connect=False)

    def secureServer(self, certFilename, keyFilename=None, keyPassword=None):
        ctx          = ssl.SSLContext(ssl.PROTOCOL_TLS)
        ctx.options |= ssl.OP_NO_TLSv1
        ctx.options |= ssl.OP_NO_TLSv1_1
        ctx.load_cert_chain(certFilename, keyFilename, keyPassword)
        self.socket  = ctx.wrap_socket(self.socket, server_side=True, do_handshake_on_connect=False)

    class HandshakeStatus(Enum):
        OK = 0
        WantRead = 1
        WantWrite = 2
        Error = 3

    def doHandshake(self):
        self.log(Etypes.Handshake)
        result = None
        try:
            self.socket.do_handshake()
            result = Connector.HandshakeStatus.OK
        except ssl.SSLWantReadError:
            result = Connector.HandshakeStatus.WantRead
        except ssl.SSLWantWriteError:
            result = Connector.HandshakeStatus.WantWrite
        # except ssl.SSLError:
        except OSError as e:
            self.log(Etypes.Error, e)
            result = Connector.HandshakeStatus.Error
        self.log(Etypes.HandshakeResult, result)
        return result

