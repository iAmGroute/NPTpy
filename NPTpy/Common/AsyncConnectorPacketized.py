
from .AsyncQueue     import AsyncQueue
from .AsyncConnector import AsyncConnector

class AsyncConnectorPacketized(AsyncConnector):

    def __init__(self, *args, **kwargs):
        AsyncConnector.__init__(self, *args, **kwargs)
        self.recvBuffer = b''
        self.lock       = AsyncQueue()

    def __repr__(self):
        return f'<AsyncConnectorPacketized {self.reprEndpoints()}>'

    async def bufferAsync(self, size):
        while len(self.recvBuffer) < size:
            data = await self.tryRecvAsync(32768)
            if data is None:
                return None
            if not data:
                self.recvBuffer = b''
                return False
            self.recvBuffer += data
        return True

    async def recvPacketAsync(self):
        async with self.lock:
            ret = await self.bufferAsync(4)
            if not ret:
                return ret
            header   = self.recvBuffer[0:4]
            totalLen = int.from_bytes(header[0:2], 'little') + 4
            ret = await self.bufferAsync(totalLen)
            if not ret:
                return ret
            packet          = self.recvBuffer[4:totalLen]
            self.recvBuffer = self.recvBuffer[totalLen:]
            return packet

    async def sendPacketAsync(self, packet):
        header  = b''
        header += len(packet).to_bytes(2, 'little')
        header += b'..'
        return await self.trySendallAsync(header + packet)

