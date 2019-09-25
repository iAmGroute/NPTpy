
from .Connector import Connector

class PacketizedConnector(Connector):

    recvBuffer = b''

    def clearBuffer(self):
        recvBuffer = b''

    def recvPacket(self):

        data = self.tryRecv(32768)
        if data is None:
            return None
        if len(data) < 1:
            return []

        packets = []
        self.recvBuffer += data
        while len(self.recvBuffer) >= 2:

            header = self.recvBuffer[0:2]
            totalLen = int.from_bytes(header[0:2], 'little') + 2

            # Check if we need more bytes to complete the packet
            if totalLen > len(self.recvBuffer):
                break

            packets.append(self.recvBuffer[2:totalLen])

            self.recvBuffer = self.recvBuffer[totalLen:]

        return packets

    def sendPacket(self, packet):
        header  = b''
        header += len(packet).to_bytes(2, 'little')
        self.sendall(header + packet)

