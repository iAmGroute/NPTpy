
import asyncio

import Globals

from .Async    import Promise
from .Loop_log import LogClass, Etypes

def reprCoroutine(c):
    res = []
    while hasattr(c, 'cr_frame') and c.cr_frame:
        line  = c.cr_frame.f_lineno
        name  = c.cr_frame.f_code.co_name
        file  = c.cr_frame.f_code.co_filename
        dot   = file.rfind('.')
        slash = file.rfind('/')
        if slash < 0: slash = file.rfind('\\')
        res.append(f'{name} {file[slash+1:dot]}:{line}')
        c = c.cr_await
    return ', '.join(res)

class Loop:

    def __init__(self):
        self.log = Globals.logger.new(LogClass)
        self.stopped    = False
        self.coroutines = {}
        self._ready     = Promise()
        self._ready()

    def stop(self):
        self.log(Etypes.Stopping)
        self.stopped    = True
        self.coroutines = {}
        self.log(Etypes.Stopped)

    def watch(self, promise):
        if self.stopped:
            return None
        future = asyncio.Future()
        self.log(Etypes.Watching, id(promise), id(future))
        promise.then(lambda *v: self._resolve(future, v))
        return future

    def _resolve(self, future, v):
        if   len(v) == 0: v = None
        elif len(v) == 1: v = v[0]
        self.log(Etypes.Resolving, id(future), v)
        future.set_result(v)
        self._ready.then(lambda: self._cont(future))

    def _cont(self, future):
        self.log(Etypes.Continuing, id(future))
        try:
            coroutine = self.coroutines[future]
            del self.coroutines[future]
        except KeyError:
            self.log(Etypes.NotFound, id(future))
        else:
            self.run(coroutine)

    def run(self, coroutine):
        if self.stopped:
            return
        cid = id(coroutine)
        self.log(Etypes.Running, cid, reprCoroutine(coroutine))
        self._ready.reset()
        try:
            future = coroutine.send(None)
            self.coroutines[future] = coroutine
        except StopIteration:
            self.log(Etypes.Finished, cid)
        except Exception as e:
            self.log(Etypes.RunError, e)
        else:
            self.log(Etypes.Paused, cid, reprCoroutine(coroutine), id(future))
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
            self.promise(result)
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

