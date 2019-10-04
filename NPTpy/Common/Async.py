
from .Generic  import identity
from .SlotList import SlotList

class Event:

    def __init__(self, oneShot=True, dataPreprocessor=identity):
        pClass = oneShot ? PromiseOneShot : Promise
        self.registrations = pClass(self, 0, dataPreprocessor, isWeak=True)
        self.disabled      = True

    def cancel(self):
        return self.registrations.cancel()

    def _cancel(self, pID):
        self.disabled = True

    def register(self, callback):
        self.disabled = False
        return self.registrations.then(callback)

    def fire(self, data):
        self.registrations._fire(data)


class Promise:

    def __init__(self, prev, myID, callback, isWeak=False):
        self.prev     = prev
        self.myID     = myID
        self.callback = callback
        self.isWeak   = isWeak
        self.next     = SlotList()
        self.value    = None

    def then(self, callback):
        p = Promise(self, -1, callback)
        pID = self.next.append(p)
        p.myID = pID
        return p

    def cancel(self):
        self.prev._cancel(self.myID)

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
        p = Promise.then(self, callback)
        if self.hasFired:
            p._fire(self.value)
        return p

    def _fire(self, data):
        if not self.hasFired:
            self.hasFired = True
            Promise._fire(self, data)
            self.cancel()

