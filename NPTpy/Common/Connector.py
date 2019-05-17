
import logging
import socket

from .Prefixes import prefixIEC
from .SmartTabs import t
from .this_OS import OS, this_OS

class Connector:

    def __init__(self, log, mySocket):
        self.log = log or logging.getLogger('dummy')
        self.socket = mySocket
        address, port = mySocket.getsockname()
        self.log.info(t('Started on\t [{0}]:{1}'.format(address, port)))

    @staticmethod
    def new(socketType=socket.SOCK_DGRAM, timeout=None, port=0, address='0.0.0.0'):
        s = socket.socket(socket.AF_INET, socketType)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind((address, port))
        return s

    def __enter__(self):
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        # if self.socket.type == socket.SOCK_STREAM:
        #     self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.log.info(t('Stopped'))

    def tryClose(self):
        try:
            self.socket.close()
        except socket.error:
            return False
        return True

    # Needed for select()
    def fileno(self):
        return self.socket.fileno()

    # Mainly UDP

    def recvfrom(self, bufferSize):
        data, addr = self.socket.recvfrom(bufferSize)
        self.log.info(t('Received {0} Bytes from\t [{1}]:{2}'.format(prefixIEC(len(data)), *addr)))
        self.log.debug(t.over('    content: {0}'.format(data)))
        return data, addr

    def sendto(self, data, endpoint):
        sentSize = self.socket.sendto(data, endpoint)
        self.log.info(t('Sent     {0} Bytes to\t [{1}]:{2}'.format(prefixIEC(sentSize), *endpoint)))
        return sentSize

    # Mainly TCP

    def listen(self):
        self.socket.listen()
        self.log.info(t('Listening'))

    def accept(self):
        conn, addr = self.socket.accept()
        self.log.info(t('Connection from\t [{0}]:{1}'.format(*addr)))
        return conn, addr

    def connect(self, endpoint):
        self.log.info(t('Connecting to\t [{0}]:{1}'.format(*endpoint)))
        self.socket.connect(endpoint)
        self.log.info(t('    connected'))

    def tryConnect(self, endpoint, data=b''):
        try:
            self.connect(endpoint)
            if data: self.sendall(data)
        except socket.error as e:
            self.log.warn(t.over('    could not connect: {0}'.format(e)))
            self.tryClose()
            return False
        return True

    def sendall(self, data):
        self.socket.sendall(data)
        self.log.info(t('Sent    \t {0} Bytes'.format(prefixIEC(len(data)))))

    def recv(self, bufferSize):
        data = self.socket.recv(bufferSize)
        self.log.info(t('Received\t {0} Bytes'.format(prefixIEC(len(data)))))
        self.log.debug(t.over('    content: {0}'.format(data)))
        return data

    def tryRecv(self, bufferSize):
        try:
            return self.recv(bufferSize)
        except socket.error:
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
        except socket.error:
            return False
        return True
