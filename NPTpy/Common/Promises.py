import weakref

from .Generic import nop, toTuple
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

    def new(self, meta=None):
        p         = Promise()
        p.myID    = self.items.append((p, False, meta))
        p.getPrev = weakref.ref(self)
        return p

    def fire(self, promiseID, params=()):
        p = self.items[promiseID]
        if p:
            p.fire(params)
            return True
        return False

    def dropAll(self):
        for k, v in self.items.iterKV():
            promise, _, _ = v
            try:
                params = self.timeoutFunction(meta)
            except AssertionError:
                pass
            else:
                promise.fire(toTuple(params))
        self.items.deleteAll()

