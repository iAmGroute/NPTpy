# The control channel
# Instead of transfering application data,
# it is used for managing the portal-client link
# and the other channels.

from Common.Futures  import Futures
from NextLoop        import loop

from .Endpoint            import Endpoint
from .ControlEndpoint_log import LogClass, Etypes

class ControlEndpoint(Endpoint):

    def __init__(self, myID, myIDF, parent, timeoutReminder):
        Endpoint.__init__(self, myID, myIDF, parent)
        self.log.upgrade(LogClass)
        self.futures = Futures(loop, timeoutReminder)

    def reset(self):
        self.futures.cancelAll()

    def send(self, data, untracked=False):
        self.parent.send(self.formMessage(data), untracked)

    def acceptMessage(self, data):
        # pylint: disable=consider-using-in
        try:
            action = data[0:1]
            if   action == b'\x00' \
              or action == b'\xFF' : pass
            elif action == b'.'    : self.actionKA(data)
            elif action == b'n'    : self.actionNewChannel(data)
            elif action == b'N'    : self.actionNewChannelReply(data)
            elif action == b'd'    : self.actionDeleteChannel(data)
            elif action == b'D'    : self.actionDeleteChannelReply(data)
            else                   : assert False, f'Unknown action: {action}'
        except (AssertionError, IndexError) as e:
            self.log(Etypes.Corrupted, e)
            self.remove()

    # Note:
    #   The prefix 'request' means we send to the other portal,
    #     and the task is done by the other portal.
    #   The prefix 'action' means we have received from the other portal,
    #     and the task is done by this portal.

    def sendKA(self):
        self.log(Etypes.SendingKA)
        self.send(b'.', True)

    def actionKA(self, data):
        self.log(Etypes.ReceivedKA, data)

    async def requestNewChannel(self, channelID, devicePort, deviceAddr):
        f, fID   = self.futures.new()
        request  = b'n...'
        request += fID.to_bytes(4, 'little')
        request += channelID.to_bytes(2, 'little')
        request += devicePort.to_bytes(2, 'little')
        request += bytes(deviceAddr, 'utf-8')
        self.send(request)
        return await f

    def actionNewChannel(self, data):
        assert len(data) > 12
        loop.run(self._actionNewChannel(data))

    async def _actionNewChannel(self, data):
        channelIDF = int.from_bytes(data[ 8:10], 'little')
        devicePort = int.from_bytes(data[10:12], 'little')
        deviceAddr = str(           data[12:],   'utf-8')
        channelID = await self.parent.newChannel(channelIDF, devicePort, deviceAddr)
        ok = channelID != 0
        self.log(Etypes.Created, ok, channelID, channelIDF)
        reply  = b'N...'
        reply += data[4: 8] # reqID
        reply += data[8:10] # channelIDF
        reply += channelID.to_bytes(2, 'little')
        self.send(reply)

    def actionNewChannelReply(self, data):
        reqID      = int.from_bytes(data[ 4: 8], 'little')
        channelID  = int.from_bytes(data[ 8:10], 'little')
        channelIDF = int.from_bytes(data[10:12], 'little')
        ok = channelIDF != 0
        self.log(Etypes.ReadyToAccept, ok, channelID, channelIDF)
        if ok:
            result = channelID, channelIDF
        else:
            result = ()
        f = self.futures.pop(reqID)
        f.ready(result)

    async def requestDeleteChannel(self, channelID, channelIDF):
        f, fID   = self.futures.new()
        request  = b'd...'
        request += fID.to_bytes(4, 'little')
        request += channelIDF.to_bytes(2, 'little')
        request += channelID.to_bytes(2, 'little')
        self.send(request)
        return await f

    def actionDeleteChannel(self, data):
        channelID  = int.from_bytes(data[ 8:10], 'little')
        channelIDF = int.from_bytes(data[10:12], 'little')
        ok = self.parent.deleteChannel(channelID)
        self.log(Etypes.DeletedByOther, ok, channelID, channelIDF)
        reply  = b'D...'
        reply += data[ 4: 8] # reqID
        reply += data[10:12] # channelIDF
        reply += b'\x01.' if ok else b'\x00.'
        self.send(reply)

    def actionDeleteChannelReply(self, data):
        reqID     = int.from_bytes(data[4: 8], 'little')
        channelID = int.from_bytes(data[8:10], 'little')
        if   data[10:12] == b'\x00.': ok = False
        elif data[10:12] == b'\x01.': ok = True
        else:                         assert False
        self.log(Etypes.DeletedByUs, ok, channelID)
        f = self.futures.pop(reqID)
        f.ready(ok, channelID)

