import weakref

from .SlotList import SlotList
from .Async    import Promise

class Selectables:

    def __init__(self):
        self.delegates = SlotList()
        self.next      = SlotList()

    def _cancel(self, promiseID):
        del self.next[promiseID]

    def _onSelect(self, delegateID):
        dRef      = self.delegates[delegateID]
        p         = Promise()
        p.myID    = self.next.append((dRef, p))
        p.getPrev = weakref.ref(self)
        return p

    def selected(self, selectables, params=()):
        for i in self.next.getIDs():
            dRef, p = self.next[i]
            d = dRef()
            if not d:
                del self.next[i]
            else:
                if d.getOwner() in selectables:
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

    def __del__(self):
        self.myModule._remove(self.myID)

    def onSelect(self):
        return self.myModule._onSelect(self.myID)

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

