
import time

from .SmartTabs import t


def getAllowList(count, enabled):
    res = [False] * count
    for item in enabled:
        res[item.value] = True
    return res


def getDenyList(count, disabled):
    res = [True] * count
    for item in disabled:
        res[item.value] = False
    return res


def getPrefix(log):
    tstamp = time.time()
    logID  = log.myID.to_bytes(4, 'big').hex().upper()
    return f'{tstamp:.1f}\t [{logID}] {log.name}:\t '


class Logger:

    def __init__(self, logPrint):
        self.logCount = 0
        self.logPrint = logPrint

    def new(self, logClass):
        logID = self.logCount
        self.logCount += 1
        return Log(self, logID, logClass)

    def logCreated(self, log):
        prefix = getPrefix(log)
        t(prefix)
        self.logPrint(t.over(f'{prefix}[Log created]'))

    def logDeleted(self, log):
        prefix = getPrefix(log)
        t(prefix)
        self.logPrint(t.over(f'{prefix}[Log deleted]'))

    def upgradeLog(self, log, newLogClass):
        prefix = getPrefix(log)
        log.setClass(newLogClass)
        t(prefix)
        self.logPrint(t.over(f'{prefix}[Upgrading to <{log.name}>]'))
        return log

    def print(self, log, ename, data):
        prefix = getPrefix(log)
        data   = f'\t {repr(data)}' if data is not None else ''
        self.logPrint(t(prefix + ename + data))


class Log:

    def __init__(self, myLogger, myID, logClass):
        self.myLogger = myLogger
        self.myID     = myID
        self.entries  = []
        self.setClass(logClass)
        if self.enabled:
            self.myLogger.logCreated(self)

    def setClass(self, logClass):
        self.name    = logClass.name
        self.etypes  = logClass.etypes
        self.enabled = logClass.enabled

    def __del__(self):
        if hasattr(self, 'myLogger'):
            if self.enabled:
                self.myLogger.logDeleted(self)

    def __call__(self, etype, *data):
        if self.enabled:
            ename, enabled, displayed = self.etypes[etype]
            if enabled:
                # self.entries.append((etype.value, repr(data)))
                pass
            if displayed:
                self.myLogger.print(self, ename, data)

    def upgrade(self, newLogClass):
        return self.myLogger.upgradeLog(self, newLogClass)


def parseEtypeValue(enabled=False, displayed=False):
    assert type(enabled)   is bool
    assert type(displayed) is bool
    return enabled, displayed


# Gathers the names and values of each variable
# in the class `etypes` and puts them in the list `res`.
# The variables in `etypes` are replaced with the index they got in `res`.
# `res` is also saved in `etypes` as `_processed`.
def parseEtypes(etypes):
    # pylint: disable=protected-access
    if not hasattr(etypes, '_processed'):
        res = []
        for etName in etypes.__dict__:
            if etName[0] != '_':
                value = parseEtypeValue(*getattr(etypes, etName))
                setattr(etypes, etName, len(res))
                res.append((etName, *value))
        etypes._processed = res
    return etypes._processed


def newClass(name, etypes, enabled=True):
    etypes = parseEtypes(etypes)
    res = type(name + '_log', (), {
        'name':    name,
        'etypes':  etypes,
        'enabled': enabled
    })
    return res


# class Log:

#     def __init__(self, path):
#         self.path     = path
#         self.contexes = {}
#         self.logType  = None

#     def __getitem__(self, name):
#         ctx = self.contexes.get(name)
#         if not ctx:
#             path = self.path + [name]
#             ctx = LogContext(path)
#             self.contexes[name] = ctx
#         return ctx()

#     def log(self, etype, data):



# class LogContext:

#     def __init__(self, path):
#         self.path        = path
#         self.nodeCounter = 0

#     def __call__(self):
#         path = self.path + [self.nodeCounter]
#         self.nodeCounter += 1
#         return Log(path)

