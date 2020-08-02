
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
            f, stale = v
            if not stale:
                self.items[k] = f, True
            else:
                del self.items[k]
                f.cancel()

    def cancelAll(self):
        for v in self.items:
            f, _ = v
            f.cancel()
        self.items.deleteAll()

    def new(self):
        f   = self.loop.newFuture()
        fID = self.items.append((f, False))
        return f, fID

    def pop(self, fID):
        item = self.items.pop(fID)
        if item is None: return DummyFuture()
        else:            return item[0]

    def get(self, fID):
        item = self.items[fID]
        if item is None: return DummyFuture()
        else:            return item[0]

