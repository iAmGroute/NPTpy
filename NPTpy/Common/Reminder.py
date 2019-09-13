import weakref

from .Generic import runAndRemove

def runDelegate(delegateRef):
    delegate = delegateRef()
    if delegate:
        delegate.run()
    return not delegate

class Reminder:

    class Delegate:

        def __init__(self, myReminder, enabled=True, skipNext=False, onRun=set(), onSkip=set()):
            self.myReminder = myReminder
            self.enabled    = enabled
            self.skipNext   = skipNext
            self.onRun      = onRun
            self.onSkip     = onSkip

        def run(self):
            if self.enabled:
                if self.skipNext:
                    self.skipNext = False
                    runAndRemove(self.onSkip, lambda f: f())
                else:
                    runAndRemove(self.onRun, lambda f: f())


    def __init__(self):
        self.delegates = set()

    def getDelegate(self, *args, **kwargs):
        d = Reminder.Delegate(self, *args, **kwargs)
        self.delegates.add(weakref.ref(d))
        return d

    def run(self):
        runAndRemove(self.delegates, runDelegate)

