
import socket
import ssl

from enum import Enum

import Globals

from .this_OS import OS, this_OS

class Etypes(Enum):
    Error           = 0
    Inited          = 1
    Deleted         = 2
    Closing         = 3
    Closed          = 4
    CloseError      = 5
    Connecting      = 6
    Connected       = 7
    Accepting       = 8
    Accepted        = 9
    Declining       = 10
    Declined        = 11
    Handshake       = 12
    HandshakeResult = 13
    Listen          = 14
    Sending         = 15
    SendingTo       = 16
    Sent            = 17
    Receiving       = 18
    Received        = 19
    ReceivedFrom    = 20
    Content         = 21


class Connector:

    def __init__(self, fromSocket=None, new=None):
        s = fromSocket if fromSocket else Connector.new(*new)
        if s.type == socket.SOCK_STREAM:
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sname = s.getsockname()
        address, port = sname[0], sname[1]
        self.socket = s
        self.log    = Globals.logger.new(Globals.LogTypes.Connector)
        self.log(Etypes.Inited, (address, port))

    @staticmethod
    def new(socketType=socket.SOCK_DGRAM, timeout=None, port=0, address='0.0.0.0', proto=0):
        af = socket.AF_INET if address.count('.') == 3 else socket.AF_INET6
        s = socket.socket(af, socketType, proto)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind((address, port))
        return s

    def __del__(self):
        try:
            self.close()
        except OSError:
            pass
        self.log(Etypes.Deleted, ())

    def __enter__(self):
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        # if self.socket.type == socket.SOCK_STREAM:
        #     self.socket.shutdown(socket.SHUT_RDWR)
        self.tryClose()

    def close(self):
        self.log(Etypes.Closing, ())
        self.socket.close()
        self.log(Etypes.Closed, ())

    def tryClose(self):
        try:
            self.close()
        except OSError as e:
            self.log(Etypes.CloseError, (repr(e)))
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.socket.fileno()

    # Mainly UDP

    def sendto(self, data, addr):
        self.log(Etypes.SendingTo, (len(data), *addr))
        self.log(Etypes.Content, (data))
        sentSize = self.socket.sendto(data, addr)
        self.log(Etypes.Sent, (sentSize))
        return sentSize

    def recvfrom(self, bufferSize):
        self.log(Etypes.Receiving, (bufferSize))
        data, addr = self.socket.recvfrom(bufferSize)
        self.log(Etypes.ReceivedFrom, (len(data), *addr))
        self.log(Etypes.Content, (data))
        return data, addr

    # Mainly TCP

    def listen(self):
        self.socket.listen()
        self.log(Etypes.Listen, ())

    def accept(self):
        self.log(Etypes.Accepting, ())
        conn, addr = self.socket.accept()
        self.log(Etypes.Accepted, (*addr,))
        return conn, addr

    def decline(self):
        self.log(Etypes.Declining, ())
        conn, addr = self.socket.accept()
        self.log(Etypes.Declined, (*addr,))
        try:
            conn.settimeout(0)
            conn.close()
        except OSError:
            pass
        return addr

    def tryAccept(self):
        try:
            conn, addr = self.accept()
        except OSError as e:
            conn, addr = None, None
            self.log(Etypes.Error, (repr(e)))
        return conn, addr

    def tryDecline(self):
        try:
            addr = self.decline()
        except OSError as e:
            addr = None
            self.log(Etypes.Error, (repr(e)))
        return addr

    def connect(self, endpoint):
        self.log(Etypes.Connecting, (*endpoint,))
        self.socket.connect(endpoint)
        self.log(Etypes.Connected, ())

    def tryConnect(self, endpoint):
        try:
            self.connect(endpoint)
        except OSError as e:
            self.log(Etypes.Error, (repr(e)))
            self.tryClose()
            return False
        return True

    def sendall(self, data):
        self.log(Etypes.Sending, (len(data)))
        self.log(Etypes.Content, (data))
        self.socket.sendall(data)
        self.log(Etypes.Sent, (len(data)))

    def trySendall(self, data):
        try:
            self.sendall(data)
            return True
        except OSError as e:
            self.log(Etypes.Error, (repr(e)))
            return False

    def recv(self, bufferSize):
        self.log(Etypes.Receiving, (bufferSize))
        data = self.socket.recv(bufferSize)
        self.log(Etypes.Received, (len(data)))
        self.log(Etypes.Content, (data))
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
                self.log(Etypes.Error, (repr(e)))
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
        self.sslContext = ssl.create_default_context(cafile=caFilename, capath=caDirpath, cadata=caData)
        self.socket     = self.sslContext.wrap_socket(self.socket, server_hostname=serverHostname, do_handshake_on_connect=False)

    def secureServer(self, certFilename, keyFilename=None, keyPassword=None):
        self.sslContext          = ssl.SSLContext(ssl.PROTOCOL_TLS)
        self.sslContext.options |= ssl.OP_NO_TLSv1
        self.sslContext.options |= ssl.OP_NO_TLSv1_1
        self.sslContext.load_cert_chain(certFilename, keyFilename, keyPassword)
        self.socket = self.sslContext.wrap_socket(self.socket, server_side=True, do_handshake_on_connect=False)

    class HandshakeStatus(Enum):
        OK = 0
        WantRead = 1
        WantWrite = 2
        Error = 3

    def doHandshake(self):
        self.log(Etypes.Handshake, ())
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
            self.log(Etypes.Error, (repr(e)))
            result = Connector.HandshakeStatus.Error
        self.log(Etypes.Handshake, (result))
        return result

