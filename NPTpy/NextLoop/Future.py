
from LogPack         import logger

from .Common         import unpack, CancelledError
from .Token          import NextToken
from .Future_log     import LogClass, Etypes


class NextFuture:

    def __init__(self, loop):
        self.log    = logger.new(LogClass)
        self.loop   = loop
        self.tokens = []
        self.result = None

    def __del__(self):
        if self.tokens:
            self.cancel()

    def _resolve(self, result):
        # pylint: disable=protected-access
        self.result = result
        for token in self.tokens:
            token.result = result
            self.loop._enqueue(token.cID)
        self.tokens = []

    def ready(self, *result):
        self.log(Etypes.Ready, *result)
        self._resolve(result)

    def cancel(self, exception=CancelledError()):
        self.log(Etypes.Cancel, exception)
        self._resolve(exception)

    def reset(self):
        self.log(Etypes.Reset)
        self.result = None

    def __await__(self):
        self.log(Etypes.Await)
        if self.result is None:
            # Return a new token, which can be held by the coroutine
            self.log(Etypes.NewToken)
            token = NextToken()
            self.tokens.append(token)
            return token.__await__()
        else:
            # Complete immediately, no token, no waiting
            return unpack(self.result)

