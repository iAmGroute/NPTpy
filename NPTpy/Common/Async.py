import weakref

from Generic   import noop
from .SlotList import SlotList

class Promise:

    def __init__(self, prev, myID, callback, isWeak=False):
        self.getPrev  = weakref.ref(prev) if prev else noop
        self.myID     = myID
        self.callback = callback
        self.isWeak   = isWeak
        self.next     = SlotList()
        self.hasFired = False
        self.value    = None

    def reset(self):
        self.hasFired = False

    def then(self, callback):
        p      = Promise(self, -1, callback, isWeak=self.isWeak)
        pID    = self.next.append(p)
        p.myID = pID
        if self.hasFired:
            p.fire(self.value)
        return p

    def cancel(self):
        prev = self.getPrev()
        if prev:
            prev._cancel(self.myID)

    def _cancel(self, pID):
        del self.next[pID]
        if self.isWeak and not self.next:
            self.cancel()

    def fire(self, data):
        self.hasFired = True
        self.value = self.callback(data)
        for p in self.next:
            p.fire(self.value)
        self.cancel()


class InstantPromise(Promise):

    def __init__(self, value):
        Promise.__init__(self, None, 0, None)
        self.hasFired = True
        self.value    = value

