
from LogPack        import logger
from Common.Generic import toTuple

from .Token         import NextToken, unpack

from .Event_log     import LogClass, Etypes


class NextEvent:

    def __init__(self, loop, f):
        self.log    = logger.new(LogClass)
        self.loop   = loop
        self.f      = f
        self.tokens = None
        self.result = None

    async def __call__(self, *args, **kwargs):
        # pylint: disable=protected-access
        self.log(Etypes.Call)
        if self.result is None:
            if self.tokens is None:
                self.log(Etypes.Await)
                self.tokens = []
                self.result = toTuple(await self.f(*args, **kwargs))
                self.log(Etypes.Resolve, self.result)
                for token in self.tokens:
                    token.result = self.result
                    self.loop._enqueue(token.cID)
                self.tokens = None
            else:
                self.log(Etypes.NewToken)
                token = NextToken()
                self.tokens.append(token)
                return await token
        return unpack(self.result)

    def isPending(self):
        return self.tokens is not None

    def isComplete(self):
        return self.result is not None

    def isPendingOrComplete(self):
        return self.tokens is not None or self.result is not None

    def reset(self):
        self.log(Etypes.Reset)
        self.result = None

