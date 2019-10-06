import weakref

from .Generic  import noop, identityMany
from .SlotList import SlotList

class Promise:

    def __init__(self, callback=identityMany):
        self.callback = callback
        self.getPrev  = noop
        self.myID     = None
        self.next     = SlotList()
        self.hasFired = False
        self.value    = None

    def reset(self):
        self.hasFired = False

    def attach(self, promise):
        p         = promise
        pID       = self.next.append(p)
        p.getPrev = weakref.ref(self)
        p.myID    = pID
        if self.hasFired:
            p.fire(self.value)
        return p

    def then(self, callback):
        return self.attach(Promise(callback))

    def thenWait(self, callback):
        return self.attach(PromiseWait(callback))

    def tee(self, callback):
        return self.attach(PromiseTee(callback))

    def cancel(self):
        prev = self.getPrev()
        if prev:
            prev._cancel(self.myID)

    def _cancel(self, pID):
        del self.next[pID]
        if not self.next:
            self.cancel()

    def fire(self, data):
        self.hasFired = True
        self.value = self.callback(*data)
        for p in self.next:
            p.fire(self.value)
        self.cancel()


def InstantPromise(value):
    p = Promise()
    p.hasFired = True
    p.value    = value
    return p


class PromiseWait(Promise):

    def __init__(self, *args, **kwargs):
        Promise.__init__(self, *args, **kwargs)
        self.hasJoined = False

    def fire(self, data):
        if self.hasJoined:
            Promise.fire(self, data)
        else:
            self.hasJoined = True
            newRoot = self.callback(*data)
            self.callback = identityMany
            self.cancel()
            newRoot.attach(self)


class PromiseTee(Promise):

    def fire(self, data):
        self.hasFired = True
        self.callback(*data)
        self.value = data
        for p in self.next:
            p.fire(data)
        self.cancel()

