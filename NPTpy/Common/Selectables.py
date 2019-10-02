import weakref

from .SlotList import SlotList

class Selectables:

    def __init__(self, capacityLog2):
        self.delegates = SlotList(capacityLog2)

    def new(self, owner, isActive, canWake):
        d = SelectablesDelegate(self, -1, owner, isActive, canWake)
        d.myID = self.delegates.append(weakref.ref(d))
        return d

    def remove(self, delegateID):
        del self.delegates[delegateID]

    def toList(self):
        ds = []
        for delegateRef in self.delegates:
            d = delegateRef()
            assert d
            ds.append(d)
        return ds

    def get(self):
        ds = self.toList()
        active     = [d.owner for d in ds if d._isActive]
        canWake    = [d.owner for d in ds if d._isActive and d._canWake]
        return active, canWake


class SelectablesDelegate:

    def __init__(self, myModule, myID, owner, _isActive, _canWake):
        self.myModule  = myModule
        self.myID      = myID
        self.owner     = owner
        self._isActive = _isActive
        self._canWake  = _canWake

    def __del__(self):
        self.myModule.remove(self.myID)

    def isActive(self):
        return self._isActive

    def on(self):
        self._isActive = True

    def off(self):
        self._isActive = False

    def canWake(self):
        return self._canWake

    def setCanWake(self):
        self._canWake = True

    def clearCanWake(self):
        self._canWake = False

