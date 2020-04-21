
from collections    import deque

from LogPack        import logger

from .Common        import CancelledError
from .Token         import NextToken
from .Queue_log     import LogClass, Etypes


class NextQueue:

    def __init__(self, loop):
        self.log    = logger.new(LogClass)
        self.loop   = loop
        self.tokens = deque()

    def __del__(self):
        self.cancel()

    async def __aenter__(self):
        self.log(Etypes.Aenter)
        if self.tokens:
            t = NextToken()
            self.tokens.append(t)
            await t
        else:
            self.tokens.append(0) # placeholder

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        # pylint: disable=protected-access
        self.log(Etypes.Aexit)
        self.tokens.popleft()
        if self.tokens:
            t        = self.tokens[0]
            t.result = ()
            self.loop._enqueue(t.cID)

    def cancel(self, exception=CancelledError()):
        # pylint: disable=protected-access
        self.log(Etypes.Cancel)
        for t in self.tokens:
            t.result = exception
            self.loop._enqueue(t.cID)
        self.tokens.clear()

