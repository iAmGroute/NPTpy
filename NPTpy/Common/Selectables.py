
import weakref

from .SlotMap import SlotMap
from .Futures import Futures


class Selectables:

    def __init__(self, loop, timeoutReminder):
        self.delegates = SlotMap()
        self.futures   = Futures(loop, timeoutReminder)

    def _onSelect(self):
        return self.futures.new()

    def selected(self, selectables, params=()):
        for dRef in self.delegates:
            d = dRef()
            if d:
                f = d.future
                if f and d.getOwner() in selectables:
                    d.future = None
                    f.ready(*params)

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
        self.future   = None

    def __del__(self):
        self.myModule._remove(self.myID)
        if self.future:
            self.future.cancel()

    def onSelect(self):
        # pylint: disable=protected-access
        self.future, _ = self.myModule._onSelect()
        return self.future

    def on(self):
        self.isActive = True

    def off(self):
        self.isActive = False

