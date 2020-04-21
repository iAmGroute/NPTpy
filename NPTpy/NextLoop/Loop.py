
from collections     import deque

from LogPack         import logger
from Common.SlotList import SlotList

from .Future         import NextFuture
from .Event          import NextEvent
from .Queue          import NextQueue
from .Loop_log       import LogClass, Etypes


def reprCoro(c):
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


class NextLoop:

    def __init__(self):
        self.log        = logger.new(LogClass)
        self.stopped    = False
        self.coroutines = SlotList()
        self.queue      = deque()
        self.empty      = True

    def stop(self):
        self.log(Etypes.Stop)
        self.stopped = True
        self.coroutines.deleteAll()
        self.queue.clear()
        self.empty   = True

    def newFuture(self):
        self.log(Etypes.NewFuture)
        return NextFuture(self)

    def newEvent(self, function):
        self.log(Etypes.NewEvent, function)
        return NextEvent(self, function)

    def newQueue(self):
        self.log(Etypes.NewQueue)
        return NextQueue(self)

    def run(self, coroutine):
        if self.stopped:
            return
        cID = self.coroutines.append(coroutine)
        self._enqueue(cID)

    def _enqueue(self, cID):
        if self.stopped:
            return
        self.log(Etypes.Enqueue, cID)
        self.queue.append(cID)
        if self.empty:
            self._run()

    def _run(self):
        # pylint: disable=broad-except
        self.empty = False
        while self.queue:
            cID = self.queue.popleft()
            c   = self.coroutines[cID]
            if c is None:
                self.log(Etypes.NotFound, cID)
            else:
                self.log(Etypes.Running, cID, reprCoro(c))
                try:
                    c.send(None).cID = cID
                    # f     = c.send(None)
                    # f.cID = cID
                except StopIteration as e:
                    self.log(Etypes.Finished, cID, e.value)
                    del self.coroutines[cID]
                except Exception as e:
                    self.log(Etypes.RunError, e)
                    del self.coroutines[cID]
                else:
                    self.log(Etypes.Paused, cID, reprCoro(c))
        self.empty = True

