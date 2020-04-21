
from LogPack        import logger

from .Common        import unpack
from .Token_log     import LogClass, Etypes


class NextToken:

    def __init__(self):
        self.log    = logger.new(LogClass)
        self.result = None
        self.cID    = -1

    def __await__(self):
        self.log(Etypes.AwaitPre)
        yield self
        self.log(Etypes.AwaitPost)
        return unpack(self.result)

