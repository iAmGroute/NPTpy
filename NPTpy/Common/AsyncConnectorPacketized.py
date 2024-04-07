
from .AsyncConnector import AsyncConnector

from NextLoop        import loop


class AsyncConnectorPacketized(AsyncConnector):

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.recvBuffer = b''
        self.lock       = loop.newQueue()

    def __repr__(self):
        return f'<AsyncConnectorPacketized {self.reprEndpoints()}>'

    async def bufferAsync(self, size, maxLoops=8, timeout=None):
        while len(self.recvBuffer) < size:
            data = await self.tryRecvAsync(32768, maxLoops, timeout)
            if data is None:
                return None
            if not data:
                self.recvBuffer = b''
                return False
            self.recvBuffer += data
        return True

    async def recvPacketAsync(self, maxLoops=8, timeout=None):
        async with self.lock:
            ret = await self.bufferAsync(4, maxLoops, timeout)
            if not ret:
                return ret
            header   = self.recvBuffer[0:4]
            totalLen = int.from_bytes(header[0:2], 'little') + 4
            ret = await self.bufferAsync(totalLen, maxLoops, timeout)
            if not ret:
                return ret
            packet          = self.recvBuffer[4:totalLen]
            self.recvBuffer = self.recvBuffer[totalLen:]
            return packet

    async def sendPacketAsync(self, packet, maxLoops=8, timeout=None):
        header  = b''
        header += len(packet).to_bytes(2, 'little')
        header += b'..'
        return await self.trySendallAsync(header + packet, maxLoops, timeout)

