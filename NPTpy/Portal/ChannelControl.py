# The control channel
# Instead of transfering application data,
# it is used for managing the portal-client link
# and the other channels.

import logging

from Common.SmartTabs import t

from .ChannelEndpoint import ChannelEndpoint

log = logging.getLogger(__name__)

class ChannelControl(ChannelEndpoint):

    def __init__(self, myID, myLink):
        ChannelEndpoint.__init__(self, myID, myLink)


    def acceptMessage(self, data):
        action = data[0:1]
        if   action == b'\x00' \
          or action == b'\xFF' : pass
        elif action == b'n'    : self.actionNewChannel(data[1:])
        elif action == b'N'    : self.actionNewChannelReply(data[1:])
        elif action == b'd'    : self.actionDeleteChannel(data[1:])
        elif action == b'D'    : self.actionDeleteChannelReply(data[1:])
        else                   : self.corrupted()


    def close(self):
        pass


    def corrupted(self):
        log.error('Link or control channel is corrupted !')
        # TODO: reset the Link


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


    def requestNewChannel(self, channelID, devicePort, deviceAddr):
        request  = b'n'
        request += channelID.to_bytes(2, 'little')
        request += devicePort.to_bytes(2, 'little')
        request += bytes(deviceAddr, 'utf-8')
        self.sendMessage(request)


    def actionNewChannel(self, data):

        if len(data) < 5:
            self.corrupted()
            return

        channelID  = int.from_bytes(data[0:2], 'little')
        devicePort = int.from_bytes(data[2:4], 'little')
        deviceAddr = str(data[4:], 'utf-8')

        ok = self.myLink.newChannel(channelID, devicePort, deviceAddr)

        self.logResult(channelID, ok, 'created')

        reply  = b'N'
        reply += data[0:2] # channelID
        reply += b'\x01' if ok else b'\x00'
        self.sendMessage(reply)


    def actionNewChannelReply(self, data):

        if len(data) != 3:
            self.corrupted()
            return

        channelID  = int.from_bytes(data[0:2], 'little')
        if   data[2:3] == b'\x00': ok = False
        elif data[2:3] == b'\x01': ok = True
        else:
            self.corrupted()
            return

        self.logResult(channelID, ok, 'ready to accept')

        if ok:
            ok = self.myLink.acceptChannel(channelID)
            self.logResult(channelID, ok, 'accepted')
        else:
            ok = self.myLink.declineChannel(channelID)
            self.logResult(channelID, ok, 'declined')


    def requestDeleteChannel(self, channelID):
        request  = b'd'
        request += channelID.to_bytes(2, 'little')
        self.sendMessage(request)

    def actionDeleteChannel(self, data):

        if len(data) != 2:
            self.corrupted()
            return

        channelID  = int.from_bytes(data[0:2], 'little')

        ok = self.myLink.deleteChannel(channelID)

        reply  = b'D'
        reply += data[0:2] # channelID
        reply += b'\x01' if ok else b'\x00'
        self.sendMessage(reply)


    def actionDeleteChannelReply(self, data):

        if len(data) != 3:
            self.corrupted()
            return

        channelID  = int.from_bytes(data[0:2], 'little')
        if   data[2:3] == b'\x00': ok = False
        elif data[2:3] == b'\x01': ok = True
        else:
            self.corrupted()
            return

        self.logResult(channelID, ok, 'deleted')

