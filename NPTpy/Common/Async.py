import weakref
import asyncio

from .Generic  import noop, identityMany, toTuple
from .SlotList import SlotList

# A very simple non-chainable promise with only 1 callback
class Todo:

    def __init__(self, now=False, action=None, params=()):
        self.now     = now
        self.action  = action
        self.params  = params

    def do(self, action):
        if self.now:
            action(*self.params)
        else:
            self.action = action

    def __call__(self, *params):
        self.now    = True
        self.params = params
        if self.action:
            self.action(*params)
            self.action = False

    def reset(self):
        self.now    = False
        self.params = ()


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
        p.myID    = self.next.append(p)
        p.getPrev = weakref.ref(self)
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

    def fire(self, params=()):
        self.hasFired = True
        self.value = self.callback(*toTuple(params))
        for p in self.next:
            p.fire(self.value)
        self.cancel()

    def __call__(self, *params):
        self.fire(params)


def InstantPromise(value):
    p = Promise()
    p.hasFired = True
    p.value    = value
    return p


class PromiseWait(Promise):

    def __init__(self, *args, **kwargs):
        Promise.__init__(self, *args, **kwargs)
        self.hasJoined = False

    def fire(self, params=()):
        if self.hasJoined:
            Promise.fire(self, params)
        else:
            self.hasJoined = True
            newRoot = self.callback(*toTuple(params))
            self.callback = identityMany
            self.cancel()
            newRoot.attach(self)


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
        self.coroutines = {}
        self.onReady    = Todo(now=True)

    def watch(self, promise):
        future = asyncio.Future()
        promise.then(lambda *v: self.cont(future, v))
        return future

    def cont(self, future, v):
        future.set_result(v)
        self.onReady.do(lambda: self._cont(future))

    def _cont(self, future):
        try:
            coroutine = self.coroutines[future]
            del self.coroutines[future]
            self.run(coroutine)
        except KeyError:
            pass

    def run(self, coroutine):
        self.onReady.reset()
        try:
            future = coroutine.send(None)
            self.coroutines[future] = coroutine
        except StopIteration:
            pass
        finally:
            self.onReady()


loop = Loop()

