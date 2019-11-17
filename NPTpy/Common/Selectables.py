import weakref

from .SlotList import SlotList
from .Async    import Promise

class SelectPromise:

    def __init__(self):
        self.next = SlotList()

    def attach(self, sDelegate, promise):
        s         = sDelegate
        p         = promise
        p.myID    = self.next.append((s, p))
        p.getPrev = weakref.ref(self)
        return p

    def _cancel(self, pID):
        del self.next[pID]

    def fire(self, selectables, params):
        for s, p in self.next:
            if s.getOwner() in selectables:
                p.fire(params)


class Selectables:

    def __init__(self):
        self.delegates = SlotList()
        self.promise   = SelectPromise()

    def _onSelect(self, delegate):
        return self.promise.attach(delegate, Promise())

    def selected(self, selectables, params=()):
        self.promise.fire(selectables, params)

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
        return self.myModule._onSelect(self)

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

