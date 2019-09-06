
import time

import ConfigFields as CF

class PortalAPI:

    def __init__(self, myPortal):
        self.myPortal = myPortal
        self.bootID   = time.time()

    def get(self):
        result           = serializePortal(self.myPortal)
        # result['bootID'] = self.bootID
        result['time']   = time.time()
        return result

    def update(self, data):
        updatePortal(self.myPortal, data)

    def process(self, context, data):
        if data and isinstance(data, dict):
            self.update(data)
        return self.get()

def updatePortal(portal, data):
    CF.update(portal, data)

def serializePortal(portal):
    return CF.serialize(portal)
