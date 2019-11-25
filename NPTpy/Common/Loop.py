
import asyncio

from .Async import Promise

class Loop:

    def __init__(self):
        self.stopped    = False
        self.coroutines = {}
        self._ready     = Promise()
        self._ready()

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


class EventAsync:

    def __init__(self, f):
        self.f = f
        self.promise  = Promise()
        self.complete = False
        self.pending  = False

    async def run(self, *args, **kwargs):
        if not self.pending and not self.complete:
            self.pending  = True
            result = await self.f(*args, **kwargs)
            self.pending  = False
            self.complete = bool(result)
            self.promise.fire(result)
            if not self.complete:
                self.promise.reset()

    async def __call__(self, *args, **kwargs):
        loop.run(self.run(*args, **kwargs))
        return await loop.watch(self.promise)

    def isPending(self):
        return self.pending

    def isComplete(self):
        return self.complete

    def isPendingOrComplete(self):
        return self.pending or self.complete

    def reset(self):
        assert not self.pending
        self.promise.reset()
        self.complete = False

