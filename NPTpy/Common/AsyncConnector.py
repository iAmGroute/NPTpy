
import socket

from errno import errorcode
from ssl   import SSLWantReadError, SSLWantWriteError

from NextLoop.Common import CancelledError

from .Connector     import Connector
from .Connector_log import Etypes


async def wait(selectable, timeout=None):
    selectable.on()
    try:
        await selectable.onSelect(timeout)
    except CancelledError:
        raise socket.timeout()
    finally:
        selectable.off()


class AsyncConnector(Connector):

    def __init__(self, readables, writables, **kwargs):
        Connector.__init__(self, **kwargs)
        self.readable = readables.new(self, False)
        self.writable = writables.new(self, False)

    def __repr__(self):
        return f'<AsyncConnector {self.reprEndpoints()}>'

    def close(self):
        self.readable.off()
        self.writable.off()
        Connector.close(self)

    async def connectAsync(self, endpoint, timeout=None):
        self.log(Etypes.Connecting, endpoint)
        self.incoming = False
        try:
            self.socket.connect(endpoint)
        except BlockingIOError:
            await wait(self.writable, timeout)
        e = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if e != 0:
            raise OSError(e, errorcode[e])
        self.log(Etypes.Connected)

    async def tryConnectAsync(self, endpoint):
        try:
            await self.connectAsync(endpoint)
            return True
        except OSError as e:
            self.log(Etypes.Error, e)
            return False

    async def sendallAsync(self, data, maxLoops=8, timeout=None):
        self.log(Etypes.Sending, len(data))
        self.log(Etypes.Content, data)
        for _ in range(maxLoops):
            try:
                self.socket.sendall(data)
            except (BlockingIOError, SSLWantWriteError):
                await wait(self.writable, timeout)
            else:
                self.log(Etypes.Sent, len(data))
                return True
        return False

    async def trySendallAsync(self, data, maxLoops=8, timeout=None):
        try:
            return await self.sendallAsync(data, maxLoops, timeout)
        except OSError as e:
            self.log(Etypes.Error, e)
            return False

    async def recvAsync(self, bufferSize, maxLoops=8, timeout=None):
        self.log(Etypes.Receiving, bufferSize)
        for _ in range(maxLoops):
            try:
                data = self.socket.recv(bufferSize)
            except (BlockingIOError, SSLWantReadError):
                await wait(self.readable, timeout)
            else:
                self.log(Etypes.Received, len(data))
                self.log(Etypes.Content, data)
                return data
        return None

    async def tryRecvAsync(self, bufferSize, maxLoops=8, timeout=None):
        try:
            return await self.recvAsync(bufferSize, maxLoops, timeout)
        except socket.timeout:
            return None
        except OSError as e:
            self.log(Etypes.Error, e)
            return b''

    async def doHandshakeAsync(self, maxLoops=8, timeout=None):
        for _ in range(maxLoops):
            result = self.doHandshake()
            if   result == Connector.HandshakeStatus.WantRead:  await wait(self.readable, timeout)
            elif result == Connector.HandshakeStatus.WantWrite: await wait(self.writable, timeout)
            elif result == Connector.HandshakeStatus.OK:        return True
            else:                                               break
        return False

    async def tryDoHandshakeAsync(self, maxLoops=8, timeout=None):
        try:
            return await self.doHandshakeAsync(maxLoops, timeout)
        except OSError as e:
            self.log(Etypes.Error, e)
            return b''

