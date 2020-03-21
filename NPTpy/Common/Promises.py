import weakref

from .Generic import nop, identityMany, toTuple
from .SlotMap import SlotMap
from .Async   import Promise

class Promises:

    def __init__(self, timeoutReminder, timeoutFunction=nop):
        self.items           = SlotMap()
        self.reminder        = timeoutReminder.new(owner=self, onRun=Promises.handleRemind)
        self.timeoutFunction = timeoutFunction

    def handleRemind(self):
        for k, v in self.items.iterKV():
            promise, stale, meta = v
            if not stale:
                self.items[k] = promise, True, meta
            else:
                del self.items[k]
                try:
                    params = self.timeoutFunction(meta)
                except AssertionError:
                    pass
                else:
                    promise.fire(toTuple(params))

    def _cancel(self, promiseID):
        del self.items[promiseID]

    def new(self, callback=identityMany, meta=None):
        p         = Promise(callback)
        p.myID    = self.items.append((p, False, meta))
        p.getPrev = weakref.ref(self)
        return p

    def fire(self, promiseID, params=()):
        item = self.items[promiseID]
        if item:
            promise, _, _ = item
            promise.fire(params)
            return True
        return False

    def dropAll(self):
        for _, v in self.items.iterKV():
            promise, _, meta = v
            try:
                params = self.timeoutFunction(meta)
            except AssertionError:
                pass
            else:
                promise.fire(toTuple(params))
        self.items.deleteAll()

