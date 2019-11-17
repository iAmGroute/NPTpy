import weakref

from .Generic  import nop
from .SlotList import SlotList

class Reminder:

    def __init__(self):
        self.delegates = SlotList()

    def _remove(self, delegateID):
        del self.delegates[delegateID]

    def new(self, *args, **kwargs):
        dID = self.delegates.append(0)
        d = ReminderDelegate(self, dID, *args, **kwargs)
        self.delegates[dID] = weakref.ref(d)
        return d

    def run(self):
        for d in self.delegates:
            delegate = d()
            if delegate:
                delegate.run()


class ReminderDelegate:

    def __init__(self, myModule, myID, enabled=True, skipNext=False, onRun=None, onSkip=None):
        self.myModule  = myModule
        self.myID      = myID
        self.enabled   = enabled
        self.skipNext  = skipNext
        self.getOnRun  = weakref.ref(onRun)  if onRun  else nop
        self.getOnSkip = weakref.ref(onSkip) if onSkip else nop

    def __del__(self):
        self.myModule._remove(self.myID)

    def run(self):
        if self.enabled:
            if self.skipNext:
                self.skipNext = False
                f = self.getOnSkip()
                if f: f()
            else:
                f = self.getOnRun()
                if f: f()

