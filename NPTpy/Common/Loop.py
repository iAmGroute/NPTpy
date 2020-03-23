
import asyncio
from collections import deque

import Globals

from .Async    import Promise
from .Loop_log import LogClass, Etypes
from .SlotList import SlotList

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
        self.coroutines = SlotList()
        self.lastID     = -1
        self.queue      = deque()

    def stop(self):
        self.log(Etypes.Stopping)
        self.stopped = True
        self.coroutines.deleteAll()
        self.queue   = deque()
        self.log(Etypes.Stopped)

    def watch(self, promise):
        if self.stopped:
            return None
        future = asyncio.Future()
        ID     = self.coroutines.append(0)
        self.log(Etypes.Watching, id(promise), ID)
        promise.then(lambda *v: self._resolve(ID, future, v))
        self.lastID = ID # don't use self.lastID in the lambda
        return future

    def _resolve(self, ID, future, v):
        if self.stopped:
            return
        if   len(v) == 0: v = None
        elif len(v) == 1: v = v[0]
        self.log(Etypes.Resolving, ID, v)
        future.set_result(v)
        self.enqueue(ID)

    def run(self, coroutine):
        if self.stopped:
            return
        ID = self.coroutines.append(coroutine)
        self.enqueue(ID)

    def enqueue(self, ID):
        self.log(Etypes.Enqueue, ID)
        now = not self.queue
        self.queue.append(ID)
        if now:
            self._run()

    def _run(self):
        while self.queue:
            ID = self.queue[0]
            c  = self.coroutines.pop(ID)
            if not c:
                self.log(Etypes.NotFound, ID)
            else:
                self.log(Etypes.Running, ID, reprCoroutine(c))
                try:
                    # while c.send(None).done(): pass
                    # while True:
                    #     future = c.send(None)
                    #     if future.done():
                    #         self.queue.popright()
                    #     else:
                    #         break
                    c.send(None)
                except StopIteration:
                    self.log(Etypes.Finished, ID)
                # except Exception as e:
                    # self.log(Etypes.RunError, e)
                else:
                    # We assume that the returned future is the last watched future
                    self.coroutines[self.lastID] = c
                    self.log(Etypes.Paused, ID, self.lastID, reprCoroutine(c))
                    self.lastID = 'dummy' # debug
            self.queue.popleft()


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

