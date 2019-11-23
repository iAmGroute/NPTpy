# The control channel
# Instead of transfering application data,
# it is used for managing the portal-client link
# and the other channels.

import logging

from Common.SmartTabs import t
from Common.SlotList  import SlotList
from Common.Async     import Promise, loop

from .Endpoint import Endpoint

log = logging.getLogger(__name__)

class ControlEndpoint(Endpoint):

    def __init__(self, myID, myIDF, parent):
        Endpoint.__init__(self, myID, myIDF, parent)
        self.promises = SlotList()

    def reset(self):
        for p in self.promises:
            p(None)
        self.promises.deleteAll()

    def send(self, data, untracked=False):
        self.parent.send(self.formMessage(data), untracked)

    def sendKA(self):
        self.send(b'.', True)

    def acceptMessage(self, data):
        if len(data) > 8:
            action = data[0:1]
            if   action == b'\x00' \
              or action == b'\xFF' : pass
            elif action == b'.'    : self.actionKA(data)
            elif action == b'n'    : self.actionNewChannel(data)
            elif action == b'N'    : self.actionNewChannelReply(data)
            elif action == b'd'    : self.actionDeleteChannel(data)
            elif action == b'D'    : self.actionDeleteChannelReply(data)
            else                   : self.corrupted()

    def corrupted(self):
        log.error('Link or control channel is corrupted !')
        self.remove()

    # Note:
    #   The prefix 'request' means we send to the other portal,
    #     and the task is done by the other portal.
    #   The prefix 'action' means we have received from the other portal,
    #     and the task is done by this portal's Link.

    def logResult(self, channelID, resultOK, whatHappened):
        if resultOK:
            log.info(t('Channel\t [{0:5d}] {1}'.format(channelID, whatHappened)))
        else:
            log.warn(t('Channel\t [{0:5d}] was NOT {1}'.format(channelID, whatHappened)))

    def actionKA(self, data):
        # Todo: log
        pass

    async def requestNewChannel(self, channelID, devicePort, deviceAddr):
        p        = Promise()
        reqID    = self.promises.append(p)
        request  = b'n...'
        request += reqID.to_bytes(4, 'little')
        request += channelID.to_bytes(2, 'little')
        request += devicePort.to_bytes(2, 'little')
        request += bytes(deviceAddr, 'utf-8')
        self.send(request)
        return await loop.watch(p)

    def actionNewChannel(self, data):
        if len(data) < 13:
            self.corrupted()
            return
        loop.run(self._actionNewChannel(data))

    async def _actionNewChannel(self, data):
        channelIDF = int.from_bytes(data[ 8:10], 'little')
        devicePort = int.from_bytes(data[10:12], 'little')
        deviceAddr = str(           data[12:],   'utf-8')
        channelID = await self.parent.newChannel(channelIDF, devicePort, deviceAddr)
        ok = channelID != 0
        self.logResult(channelID, ok, 'created')
        log.info(t('    remote ID\t [{0:5d}]'.format(channelIDF)))
        reply  = b'N...'
        reply += data[4: 8] # reqID
        reply += data[8:10] # channelIDF
        reply += channelID.to_bytes(2, 'little')
        self.send(reply)

    def actionNewChannelReply(self, data):
        if len(data) != 12:
            self.corrupted()
            return
        reqID      = int.from_bytes(data[ 4: 8], 'little')
        channelID  = int.from_bytes(data[ 8:10], 'little')
        channelIDF = int.from_bytes(data[10:12], 'little')
        ok = channelIDF != 0
        self.logResult(channelID, ok, 'ready to accept')
        if ok:
            log.info(t('    remote ID\t [{0:5d}]'.format(channelIDF)))
            result = channelID, channelIDF
        else:
            result = None
        p = self.promises[reqID]
        if p:
            self.promises[reqID] = None
            p(result)

    async def requestDeleteChannel(self, channelID, channelIDF):
        p        = Promise()
        reqID    = self.promises.append(p)
        request  = b'd...'
        request += reqID.to_bytes(4, 'little')
        request += channelIDF.to_bytes(2, 'little')
        request += channelID.to_bytes(2, 'little')
        self.send(request)
        return await loop.watch(p)

    def actionDeleteChannel(self, data):
        if len(data) != 12:
            self.corrupted()
            return
        channelID  = int.from_bytes(data[ 8:10], 'little')
        channelIDF = int.from_bytes(data[10:12], 'little')
        ok = self.parent.deleteChannel(channelID)
        self.logResult(channelID, ok, 'deleted by other')
        reply  = b'D...'
        reply += data[ 4: 8] # reqID
        reply += data[10:12] # channelIDF
        reply += b'\x01.' if ok else b'\x00.'
        self.send(reply)

    def actionDeleteChannelReply(self, data):
        if len(data) != 12:
            self.corrupted()
            return
        reqID     = int.from_bytes(data[4: 8], 'little')
        channelID = int.from_bytes(data[8:10], 'little')
        if   data[10:12] == b'\x00.': ok = False
        elif data[10:12] == b'\x01.': ok = True
        else:
            self.corrupted()
            return
        self.logResult(channelID, ok, 'deleted by us')
        p = self.promises[reqID]
        if p:
            del self.promises[reqID]
            p(ok, channelID)

