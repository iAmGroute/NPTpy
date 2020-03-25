
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
                    c.send(None).cID = cID
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
        self.tokens = []
        self.result = None

    def __del__(self):
        if self.tokens:
            self.cancel()

    def _resolve(self, result):
        self.result = result
        for token in self.tokens:
            token.result = result
            self.myLoop._enqueue(token.cID)
        self.tokens = []

    def ready(self, *result):
        self.log(EtypesF.Ready, *result)
        self._resolve(result)

    def cancel(self, exception=CancelledError()):
        self.log(EtypesF.Cancel, exception)
        self._resolve(exception)

    def reset(self):
        self.log(EtypesF.Reset)
        self.result = None

    def __await__(self):
        self.log(EtypesF.Await)
        if self.result is None:
            # Return a new token, which can be held by the coroutine
            token = NextToken()
            self.tokens.append(token)
            return token.__await__()
        else:
            # Complete immediately, no token, no waiting
            return _unpack(self.result)


# One per await, owned by the NextFuture and also
# held by the coroutine that awaits it.
class NextToken:

    def __init__(self):
        self.result = None
        self.cID    = -1

    def __await__(self):
        yield self
        return _unpack(self.result)


def _unpack(result):
    if type(result) is tuple:
        # The actual value to return has been packed by a foo(*result) call
        l = len(result)
        if   l == 0: return None
        elif l == 1: return result[0]
        else:        return result
    else:
        # Result is exception
        raise result


loop = NextLoop()

