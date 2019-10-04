import weakref

from .Generic  import noop, identity
from .SlotList import SlotList

class Event:

    def __init__(self, oneShot=True, preprocessor=identity, onDelete=noop):
        pClass = PromiseOneShot if oneShot else Promise
        self.registrations = pClass(self, 0, preprocessor, isWeak=True)
        self.onDelete      = onDelete
        self.disabled      = True

    def __del__(self):
        self.onDelete(self)

    def cancel(self):
        return self.registrations.cancel()

    def _cancel(self, pID):
        self.disabled = True

    def then(self, callback):
        self.disabled = False
        return self.registrations.then(callback)

    def fire(self, data=None):
        self.registrations._fire(data)

    def isOneShot(self):
        return type(self.registrations) is PromiseOneShot

    def reset(self):
        if self.isOneShot():
            self.registrations.hasFired = False


class Promise:

    def __init__(self, prev, myID, callback, isWeak=False):
        self.getPrev  = weakref.ref(prev)
        self.myID     = myID
        self.callback = callback
        self.isWeak   = isWeak
        self.next     = SlotList()
        self.value    = None

    def then(self, callback, pClass=None):
        pClass = pClass if pClass else Promise
        p = pClass(self, -1, callback)
        pID = self.next.append(p)
        p.myID = pID
        return p

    def cancel(self):
        prev = self.getPrev()
        if prev:
            prev._cancel(self.myID)

    def _cancel(self, pID):
        del self.next[pID]
        if self.isWeak and not self.next:
            self.cancel()

    def _fire(self, data):
        self.value = self.callback(data)
        for p in self.next:
            p._fire(self.value)


class PromiseOneShot(Promise):

    def __init__(self, *args, **kwargs):
        Promise.__init__(self, *args, **kwargs)
        self.hasFired = False

    def then(self, callback):
        p = Promise.then(self, callback, PromiseOneShot)
        if self.hasFired:
            p._fire(self.value)
        return p

    def _fire(self, data):
        if not self.hasFired:
            self.hasFired = True
            Promise._fire(self, data)
            self.cancel()


class InstantPromise(PromiseOneShot):

    def __init__(self, value):
        PromiseOneShot.__init__(self, self, 0, None)
        self.hasFired = True
        self.value    = value

