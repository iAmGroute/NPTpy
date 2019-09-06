
import time

import ConfigFields as CF

class PortalAPI:

    def __init__(self, myPortal, portalConfig):
        self.myPortal     = myPortal
        self.portalConfig = portalConfig
        self.bootID       = time.time()

    def get(self):
        r = {}
        r['bootID'] = self.bootID
        r['time']   = time.time()
        r['store']  = serializePortal(self.myPortal)
        return r

    def update(self, data):
        bootID   = data.get('bootID')
        prevTime = data.get('time')
        store    = data.get('store')
        save     = data.get('save')
        assert bootID == self.bootID,           'There must not be a reboot since last refresh'
        assert 0 < time.time() - prevTime < 10, 'Update must be based on recent data (<10seconds old)'
        updatePortal(self.myPortal, store)
        if save is True:
            self.portalConfig.scanAndSave(self.myPortal)

    def process(self, context, data):
        if isinstance(data, dict) and data:
            self.update(data)
        return self.get()

def updatePortal(portal, store):
    if isinstance(store, dict):
        CF.update(portal, store)

def serializePortal(portal):
    return CF.serialize(portal)
