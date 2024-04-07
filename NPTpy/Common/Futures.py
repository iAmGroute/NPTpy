
from typing import Optional, Tuple

from NextLoop.Loop   import NextLoop
from NextLoop.Future import NextFuture

from .SlotList      import SlotList
from .TimedReminder import TimedReminder


class Futures:

    def __init__(self, loop: NextLoop, reminder: TimedReminder):
        self.loop     = loop
        self.reminder = reminder.new(owner=self, onRun=Futures.handleRemind)
        self._futures = SlotList[Tuple[NextFuture, Optional[int]]]()

    def handleRemind(self):
        for k, (ftr, timeout) in self._futures.items_mutable():
            if timeout is not None:
                if timeout > 0:
                    self._futures[k] = ftr, timeout - 1
                else:
                    del self._futures[k]
                    ftr.cancel()

    def cancelAll(self):
        for (ftr, _) in self._futures:
            ftr.cancel()
        self._futures.clear()

    def new(self, timeout :Optional[int] = None):
        ftr = self.loop.newFuture()
        key = self._futures.append((ftr, timeout))
        return ftr, key

    def pop(self, key: int):
        x = self._futures.pop(key)
        if x is None: return NextFuture().cancel()
        else:         return x[0]

    def get(self, key: int):
        x = self._futures[key]
        if x is None: return NextFuture().cancel()
        else:         return x[0]

