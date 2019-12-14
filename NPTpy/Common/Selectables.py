import weakref

from .SlotList import SlotList
from .Promises import Promises

class Selectables:

    def __init__(self, timeoutReminder):
        self.delegates = SlotList()
        self.promises  = Promises(timeoutReminder)

    def _onSelect(self):
        return self.promises.new()

    def selected(self, selectables, params=()):
        for dRef in self.delegates:
            d = dRef()
            if d:
                p = d.promise
                if p and d.getOwner() in selectables:
                    d.promise = None
                    p.fire(params)

    def new(self, owner, isActive, canWake):
        dID = self.delegates.append(0)
        d = SelectablesDelegate(self, dID, owner, isActive, canWake)
        self.delegates[dID] = weakref.ref(d)
        return d

    def _remove(self, delegateID):
        del self.delegates[delegateID]

    def toList(self):
        ds = []
        for delegateRef in self.delegates:
            d = delegateRef()
            assert d
            ds.append(d)
        return ds

    def get(self):
        ds      = self.toList()
        active  = [d.getOwner() for d in ds if d._isActive]
        canWake = [d.getOwner() for d in ds if d._isActive and d._canWake]
        return active, canWake


class SelectablesDelegate:

    def __init__(self, myModule, myID, owner, _isActive, _canWake):
        self.myModule  = myModule
        self.myID      = myID
        self.getOwner  = weakref.ref(owner)
        self._isActive = _isActive
        self._canWake  = _canWake
        self.promise   = None

    def __del__(self):
        if self.promise:
            self.promise.cancel()
        self.myModule._remove(self.myID)

    def onSelect(self):
        # TODO: keep ID instead
        self.promise = self.myModule._onSelect()
        return self.promise

    def isActive(self):
        return self._isActive

    def on(self):
        self._isActive = True

    def off(self):
        self._isActive = False

    def canWake(self):
        return self._canWake

    def yesWake(self):
        self._canWake = True

    def noWake(self):
        self._canWake = False

