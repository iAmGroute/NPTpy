
from .AsyncQueue     import AsyncQueue
from .AsyncConnector import AsyncConnector

class AsyncConnectorPacketized(AsyncConnector):

    def __init__(self, *args, **kwargs):
        AsyncConnector.__init__(self, *args, **kwargs)
        self.recvBuffer = b''
        self.lock       = AsyncQueue()

    async def bufferAsync(self, size):
        while len(self.recvBuffer) < size:
            data = await self.tryRecvAsync(32768)
            if not data:
                return False
            self.recvBuffer += data
        return True

    async def recvPacketAsync(self):
        async with self.lock:
            if not await self.bufferAsync(4):
                return None
            header   = self.recvBuffer[0:4]
            totalLen = int.from_bytes(header[0:2], 'little') + 4
            if not await self.bufferAsync(totalLen):
                return None
            packet          = self.recvBuffer[4:totalLen]
            self.recvBuffer = self.recvBuffer[totalLen:]
            return packet

    async def sendPacketAsync(self, packet):
        header  = b''
        header += len(packet).to_bytes(2, 'little')
        header += b'..'
        await self.sendallAsync(header + packet)

