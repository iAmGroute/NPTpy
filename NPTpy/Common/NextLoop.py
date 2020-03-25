
from collections import deque

import Globals

from .SlotList     import SlotList
from .NextLoop_log import LogClassL, EtypesL, \
                          LogClassF, EtypesF


class CancelledError(Exception):
    pass


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
        self.log = Globals.logger.new(LogClassL)
        self.stopped    = False
        self.coroutines = SlotList()
        self.queue      = deque()
        self.empty      = True

    def stop(self):
        self.log(EtypesL.Stop)
        self.stopped = True
        self.coroutines.deleteAll()
        self.queue.clear()
        self.empty   = True

    def newFuture(self):
        f = NextFuture(self)
        self.log(EtypesL.NewFuture, id(f))
        return f

    def run(self, coroutine):
        if self.stopped:
            return
        cID = self.coroutines.append(coroutine)
        self._enqueue(cID, None)

    def _enqueue(self, cID):
        if self.stopped:
            return
        self.log(EtypesL.Enqueue, cID)
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
                self.log(EtypesL.NotFound, cID)
            else:
                self.log(EtypesL.Running, cID, reprCoro(c))
                try:
                    c.send(None).cIDs.append(cID)
                    # f     = c.send(None)
                    # f.cID = cID
                except StopIteration as e:
                    self.log(EtypesL.Finished, cID, e.value)
                    del self.coroutines[cID]
                except Exception as e:
                    self.log(EtypesL.RunError, e)
                    del self.coroutines[cID]
                else:
                    self.log(EtypesL.Paused, cID, reprCoro(c))
        self.empty = True


class NextFuture:

    def __init__(self, myLoop):
        self.log    = Globals.logger.new(LogClassF)
        self.myLoop = myLoop
        self.cIDs   = []
        self.result = None

    def ready(self, *result):
        self.log(EtypesF.Ready, *result)
        self.result = result
        for cID in self.cIDs:
            self.myLoop._enqueue(cID)
        self.cIDs = []

    def cancel(self, exception=CancelledError()):
        self.log(EtypesF.Cancel, exception)
        self.result = exception
        for cID in self.cIDs:
            self.myLoop._enqueue(cID)
        self.cIDs = []

    def __await__(self):
        self.log(EtypesF.Await)
        while self.result is None:
            yield self
        # if self.result is None:
        #     # Called twice with no result,
        #     # so it has been reused or called without await.
        #     raise RuntimeError('You should `await` this future and only once')
        # Reset all our fields to avoid holding references
        # result = self.result
        # self.cID    = -1
        # self.result = None
        self.log(EtypesF.AwaitDone, self.result)
        if type(self.result) is tuple:
            return self.result
        else:
            # Result is exception
            raise self.result


loop = NextLoop()

