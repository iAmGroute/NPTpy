import weakref
import asyncio

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
        self.hasFired = True
        self.value = self.callback(*toTuple(params))
        for p in self.next:
            p.fire(self.value)
        self.cancel()

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


class PromiseTee(Promise):

    def fire(self, params=()):
        self.hasFired = True
        self.callback(*toTuple(params))
        self.value = params
        for p in self.next:
            p.fire(params)
        self.cancel()


class Loop:

    def __init__(self):
        self.stopped    = False
        self.coroutines = {}
        self._ready   = Promise()
        self._ready()

    def stop(self):
        self.stopped    = True
        self.coroutines = {}

    def stop(self):
        self.stopped    = True
        self.coroutines = {}

    def watch(self, promise):
        if self.stopped:
            return None
        future = asyncio.Future()
        promise.then(lambda *v: self._resolve(future, v))
        return future

    def _resolve(self, future, v):
        if   len(v) == 0: v = None
        elif len(v) == 1: v = v[0]
        future.set_result(v)
        self._ready.then(lambda: self._cont(future))

    def _cont(self, future):
        try:
            coroutine = self.coroutines[future]
            del self.coroutines[future]
            self.run(coroutine)
        except KeyError:
            pass

    def run(self, coroutine):
        if self.stopped:
            return
        self._ready.reset()
        try:
            future = coroutine.send(None)
            self.coroutines[future] = coroutine
        except StopIteration:
            pass
        finally:
            self._ready()


loop = Loop()


# class Event:

#     def __init__(self, fStart, fCancel=nop, fAfter=identityMany):
#         self.fStart  = fStart
#         self.fCancel = fCancel
#         self.promise = Promise(fAfter)
#         self.pending = False

#     def isPending(self):
#         return self.pending

#     def isComplete(self):
#         return self.promise.hasFired

#     def start(self):
#         if not self.pending and not self.isComplete():
#             ok = self.fStart()
#             if not ok:
#                 return None
#             self.pending = True
#         return self.promise

#     def cancel(self):
#         if self.pending:
#             ok = self.fCancel()
#             if not ok:
#                 return False
#             self.pending = False
#         self.promise.reset()
#         self.promise.cancel()
#         return True

#     def complete(self, *params):
#         if self.pending:
#             self.pending = False
#             self.promise.fire(params)

#     async def __call__(self):
#         p = self.start()
#         return (await loop.watch(p)) if p else None


class EventAsync:

    def __init__(self, f):
        self.f = f
        self.promise = Promise()
        self.pending = False

    async def __call__(self, *args, **kwargs):
        if not self.isPendingOrComplete():
            self.pending = True
            result = await self.f(*args, **kwargs)
            self.promise.fire(result)
            self.pending = False
            if not result:
                self.reset()
            return result
        elif self.pending:
            return await loop.watch(self.promise)
        else:
            return self.promise.value

    def isPending(self):
        return self.pending

    def isComplete(self):
        return self.promise.hasFired

    def isPendingOrComplete(self):
        return self.pending or self.promise.hasFired

    def reset(self):
        self.promise.reset()

