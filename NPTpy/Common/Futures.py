
from .SlotMap  import SlotMap
from .NextLoop import loop, CancelledError


class DummyFuture:

    def ready(self, *params):
        pass

    def cancel(self, *params):
        pass

    def reset(self):
        pass

    def __await__(self):
        raise CancelledError()


class Futures:

    def __init__(self, timeoutReminder):
        self.items    = SlotMap()
        self.reminder = timeoutReminder.new(owner=self, onRun=Futures.handleRemind)

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
        f   = loop.newFuture()
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

