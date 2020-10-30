
from .SlotMap        import SlotMap

from NextLoop.Common import CancelledError


class DummyFuture:

    def ready(self, *result):
        pass

    def cancel(self, exception=None):
        pass

    def reset(self):
        pass

    def __await__(self):
        raise CancelledError()


class Futures:

    def __init__(self, loop, timeoutReminder):
        self.loop     = loop
        self.reminder = timeoutReminder.new(owner=self, onRun=Futures.handleRemind)
        self.items    = SlotMap()

    def handleRemind(self):
        for k, v in self.items.iterKV():
            f, timeout = v
            if timeout is not None:
                if timeout > 0:
                    self.items[k] = f, timeout - 1
                else:
                    del self.items[k]
                    f.cancel()

    def cancelAll(self):
        for v in self.items:
            f, _ = v
            f.cancel()
        self.items.deleteAll()

    def new(self, timeout=None):
        f   = self.loop.newFuture()
        fID = self.items.append((f, timeout))
        return f, fID

    def pop(self, fID):
        item = self.items.pop(fID)
        if item is None: return DummyFuture()
        else:            return item[0]

    def get(self, fID):
        item = self.items[fID]
        if item is None: return DummyFuture()
        else:            return item[0]

