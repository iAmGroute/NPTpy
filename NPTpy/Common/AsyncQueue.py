from collections import deque

from .Async import Promise
from .Loop  import loop

class AsyncQueue:

    def __init__(self):
        self.queue = deque()

    async def __aenter__(self):
        if self.queue:
            p = Promise()
            self.queue.append(p)
            await loop.watch(p)
        else:
            self.queue.append(0) # placeholder

    async def __aexit__(self, type=None, value=None, traceback=None):
        self.queue.popleft()
        if self.queue:
            p = self.queue[0]
            p.fire()

