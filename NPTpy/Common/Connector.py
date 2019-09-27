
import logging
import socket
import ssl
from enum import Enum

from .Prefixes import prefixIEC
from .SmartTabs import t
from .this_OS import OS, this_OS

# Log levels:
#  - 25: State changes (Started, Stopped)
#  - 23: Connections initiated by us, outgoing (Connecting to)
#  - 21: Connections accepted, incoming (Connection from)
#  - 20: Connections declined, incoming (Connection from)
#  - 19: TLS handshake state changes (Complete, Error)
#  - 18: TLS handshake update (Start/Resume)
#  - 17: Exception in tryClose()
#  - 15: Exception in TCP try send and receive
#  - 12: UDP send and receive
#  - 10: TCP send and receive
#  -  7: UDP content
#  -  5: TCP content
#  -  4: TLS handshake state progress (WantRead, WantWrite)
#  -  3: State change progress (Starting, Stopping)

class Connector:

    def __init__(self, log, mySocket):
        self.log = log or logging.getLogger('dummy')
        self.socket = mySocket
        self.log.log(3, t('Starting'))
        if mySocket.type == socket.SOCK_STREAM:
            mySocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sname = mySocket.getsockname()
        address, port = sname[0], sname[1]
        self.log.log(25, t('Started on\t [{0}]:{1}'.format(address, port)))

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

    def __enter__(self):
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        # if self.socket.type == socket.SOCK_STREAM:
        #     self.socket.shutdown(socket.SHUT_RDWR)
        self.tryClose()

    def close(self):
        self.log.log(3, t('Stopping'))
        self.socket.close()
        self.log.log(25, t('Stopped'))

    def tryClose(self):
        try:
            self.close()
        except OSError as e:
            self.log.log(17, t.over('Could not close: {0}'.format(e)))
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.socket.fileno()

    # Mainly UDP

    def sendto(self, data, endpoint):
        sentSize = self.socket.sendto(data, endpoint)
        self.log.log(12, t('Sent     {0} Bytes to\t [{1}]:{2}'.format(prefixIEC(sentSize), *endpoint)))
        self.log.log( 7, t.over('    content: {0}'.format(data.hex().upper())))
        return sentSize

    def recvfrom(self, bufferSize):
        data, addr = self.socket.recvfrom(bufferSize)
        self.log.log(12, t('Received {0} Bytes from\t [{1}]:{2}'.format(prefixIEC(len(data)), *addr)))
        self.log.log( 7, t.over('    content: {0}'.format(data.hex().upper())))
        return data, addr

    # Mainly TCP

    def listen(self):
        self.socket.listen()
        self.log.log(25, t('Listening'))

    def accept(self):
        self.log.log(21, t('Accepting incoming'))
        conn, addr = self.socket.accept()
        self.log.log(21, t('Connection from\t [{0}]:{1}'.format(*addr)))
        return conn, addr

    def decline(self):
        self.log.log(20, t('Declining incoming'))
        conn, addr = self.socket.accept()
        self.log.log(20, t('Connection from\t [{0}]:{1}'.format(*addr)))
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
            self.log.log(21, t.over('    accept error: {0}'.format(e)))
        return conn, addr

    def tryDecline(self):
        try:
            addr = self.decline()
        except OSError as e:
            addr = None
            self.log.log(20, t.over('    decline error: {0}'.format(e)))
        return addr

    def connect(self, endpoint):
        self.log.log(23, t('Connecting to\t [{0}]:{1}'.format(*endpoint)))
        self.socket.connect(endpoint)
        self.log.log(23, t('    connected'))

    def tryConnect(self, endpoint):
        try:
            self.connect(endpoint)
        except OSError as e:
            self.log.log(23, t.over('    could not connect: {0}'.format(e)))
            self.tryClose()
            return False
        return True

    def sendall(self, data):
        self.socket.sendall(data)
        self.log.log(10, t('Sent    \t {0} Bytes'.format(prefixIEC(len(data)))))
        self.log.log(5, t.over('    content: {0}'.format(data.hex().upper())))

    def trySendall(self, data):
        try:
            self.sendall(data)
            return True
        except OSError as e:
            self.log.log(15, t.over('Could not send: {0}'.format(e)))
            return False

    def recv(self, bufferSize):
        data = self.socket.recv(bufferSize)
        self.log.log(10, t('Received\t {0} Bytes'.format(prefixIEC(len(data)))))
        self.log.log(5, t.over('    content: {0}'.format(data.hex().upper())))
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
                self.log.log(15, t.over('Could not receive: {0}'.format(e)))
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
        self.log.log(18, t('Handshake:\t Start/Resume'))
        try:
            self.socket.do_handshake()
            self.log.log(19, t('Handshake:\t Complete'))
            return Connector.HandshakeStatus.OK
        except ssl.SSLWantReadError:
            self.log.log(18, t('Handshake:\t Need to read more'))
            return Connector.HandshakeStatus.WantRead
        except ssl.SSLWantWriteError:
            self.log.log(18, t('Handshake:\t Need to write more'))
            return Connector.HandshakeStatus.WantWrite
        # except ssl.SSLError:
        except OSError as e:
            self.log.log(19, t('Handshake:\t Error'))
            self.log.log(19, t.over('\t {0}'.format(e)))
            return Connector.HandshakeStatus.Error

