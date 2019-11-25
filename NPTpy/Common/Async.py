
import weakref

from .Generic  import nop, identityMany, toTuple
from .SlotList import SlotList

class Promise:

    def __init__(self, callback=identityMany):
        self.callback = callback
        self.getPrev  = nop
        self.myID     = None
        self.next     = SlotList()
        self.hasFired = False
        self.value    = None

    def __del__(self):
        if not self.hasFired:
            self.fire()

    def reset(self):
        self.hasFired = False

    def attach(self, promise):
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

    def cancel(self):
        prev = self.getPrev()
        if prev:
            prev._cancel(self.myID)
        for p in self.next:
            p.cancel()

    def _cancel(self, pID):
        del self.next[pID]
        if not self.next:
            self.cancel()

    def fire(self, params=()):
        self.cancel()
        self.hasFired = True
        self.value    = self.callback(*toTuple(params))
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
#             newRoot = self.callback(*toTuple(params))
#             self.callback = identityMany
#             self.cancel()
#             newRoot.attach(self)


# class PromiseTee(Promise):

#     def fire(self, params=()):
#         self.hasFired = True
#         self.callback(*toTuple(params))
#         self.value = params
#         for p in self.next:
#             p.fire(params)
#         self.cancel()

