
import weakref

import Globals

from .Generic   import nop, identityMany, toTuple
from .SlotList  import SlotList
from .Async_log import LogClass, Etypes

class Promise:

    def __init__(self, callback=identityMany):
        self.log      = Globals.logger.new(LogClass)
        self.callback = callback
        self.getPrev  = nop
        self.myID     = None
        self.next     = SlotList()
        self.hasFired = False
        self.value    = None
        self.log(Etypes.Inited, id(self), callback)

    def __del__(self):
        if hasattr(self, 'log'):
            self.log(Etypes.Deleting)
        if not self.hasFired:
            self.fire()

    def reset(self):
        self.log(Etypes.Reset)
        self.hasFired = False

    def attach(self, promise):
        self.log(Etypes.Attach, id(promise))
        p         = promise
        p.myID    = self.next.append(p)
        p.getPrev = weakref.ref(self)
        if self.hasFired:
            p.fire(self.value)
        return p

    def then(self, callback):
        return self.attach(Promise(callback))

    # def thenWait(self, callback):
    #     return self.attach(PromiseWait(callback))

    # def tee(self, callback):
    #     return self.attach(PromiseTee(callback))

    def detach(self):
        self.log(Etypes.Detach)
        prev = self.getPrev()
        if prev:
            prev._cancel(self.myID)

    def cancel(self):
        self.detach()
        for p in self.next:
            p.cancel()

    def _cancel(self, pID):
        del self.next[pID]
        if not self.next:
            self.detach()

    def fire(self, params=()):
        self.log(Etypes.Fire, *params)
        self.detach()
        self.hasFired = True
        self.value    = toTuple(self.callback(*params))
        self.log(Etypes.FireResult, *self.value)
        for p in self.next:
            p.fire(self.value)

    def __call__(self, *params):
        self.fire(params)


# def InstantPromise(value):
#     p = Promise()
#     p.hasFired = True
#     p.value    = value
#     return p


# class PromiseWait(Promise):

#     def __init__(self, *args, **kwargs):
#         Promise.__init__(self, *args, **kwargs)
#         self.hasJoined = False

#     def fire(self, params=()):
#         if self.hasJoined:
#             Promise.fire(self, params)
#         else:
#             self.hasJoined = True
#             newRoot = self.callback(*params)
#             self.callback = identityMany
#             self.cancel()
#             newRoot.attach(self)


# class PromiseTee(Promise):

#     def fire(self, params=()):
#         self.hasFired = True
#         self.callback(*params)
#         self.value = params
#         for p in self.next:
#             p.fire(params)
#         self.cancel()

