import weakref

from .SlotMap  import SlotMap
from .Promises import Promises

class Selectables:

    def __init__(self, timeoutReminder):
        self.delegates = SlotMap()
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

    def new(self, owner, isActive):
        dID = self.delegates.append(0)
        d = SelectablesDelegate(self, dID, owner, isActive)
        self.delegates[dID] = weakref.ref(d)
        return d

    def _remove(self, delegateID):
        del self.delegates[delegateID]

    def get(self):
        ds = []
        for delegateRef in self.delegates:
            d = delegateRef()
            if d and d.isActive:
                ds.append(d.getOwner())
        return ds


class SelectablesDelegate:

    def __init__(self, myModule, myID, owner, isActive):
        self.myModule = myModule
        self.myID     = myID
        self.getOwner = weakref.ref(owner)
        self.isActive = isActive
        self.promise  = None

    def __del__(self):
        if self.promise:
            self.promise.cancel()
        self.myModule._remove(self.myID)

    def onSelect(self):
        # pylint: disable=protected-access
        self.promise = self.myModule._onSelect()
        return self.promise

    def on(self):
        self.isActive = True

    def off(self):
        self.isActive = False

