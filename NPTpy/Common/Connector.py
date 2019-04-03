
import logging
import socket

from .Prefixes import prefixIEC
from .SmartTabs import t

class Connector:

    def __init__(self, log=None, socketType=socket.SOCK_DGRAM, timeout=None, port=0, address='0.0.0.0'):
        self.log = log or logging.getLogger('dummy')
        s = socket.socket(socket.AF_INET, socketType)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(timeout)
        s.bind((address, port))
        self.socket = s
        self.log.info(t('Started on\t [{0}]:{1}'.format(address, port)))

    def __enter__(self):
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        # if self.socket.type == socket.SOCK_STREAM:
        #     self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.log.info(t('Stopped'))

    # Mainly UDP

    def recvfrom(self, bufferSize):
        data, addr = self.socket.recvfrom(bufferSize)
        self.log.info(t('Received {0}Bytes from\t [{1}]:{2}'.format(prefixIEC(len(data)), *addr)))
        self.log.debug(t.over('    content: {0}'.format(data)))
        return data, addr

    def sendto(self, data, endpoint):
        sentSize = self.socket.sendto(data, endpoint)
        self.log.info(t('Sent     {0}Bytes to\t [{1}]:{2}'.format(prefixIEC(sentSize), *endpoint)))
        return sentSize

    # Mainly TCP

    def listen(self):
        self.socket.listen()
        self.log.info(t('Listening'))

    def accept(self):
        conn, addr = self.socket.accept()
        self.log.info(t('Connection from\t [{0}]:{1}'.format(*addr)))
        return conn, addr

    def recv(self, bufferSize):
        data = self.socket.recv(bufferSize)
        self.log.info(t('Received {0} Bytes'.format(prefixIEC(len(data)))))
        self.log.debug(t.over('    content: {0}'.format(data)))
        return data

    def connect(self, endpoint):
        self.socket.connect(endpoint)
        self.log.info(t('Connected to\t [{0}]:{1}'.format(*endpoint)))

    def sendall(self, data):
        self.socket.sendall(data)
        self.log.info(t('Sent     {0}Bytes'.format(prefixIEC(len(data)))))
