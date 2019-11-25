
import time

from enum import Enum

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
    tstamp  = time.time()
    logID   = log.myID.to_bytes(4, 'big').hex().upper()
    logName = log.logClass.name
    return f'{tstamp:.1f}\t [{logID}] {logName}:\t '


class Logger:

    def __init__(self):
        self.logCount = 0

    def processLogClass(self, logClass):
        if not hasattr(logClass, 'enList'):
            m = 0
            for et in logClass.etypes:
                assert type(et.value) is int
                assert et.value > 0
                if et.value > m:
                    m = et.value
            m += 1
            if   hasattr(logClass, 'enabled'):  eL = getAllowList(m, logClass.enabled)
            elif hasattr(logClass, 'disabled'): eL = getDenyList(m, logClass.disabled)
            else:                               eL = getDenyList(m, {})
            logClass.enList = eL

    def new(self, logClass):
        self.processLogClass(logClass)
        logID = self.logCount
        self.logCount += 1
        return Log(self, logID, logClass)

    def logCreated(self, log):
        prefix = getPrefix(log)
        t(prefix)
        print(t.over(f'{prefix}[Log created]'))

    def logDeleted(self, log):
        prefix = getPrefix(log)
        t(prefix)
        print(t.over(f'{prefix}[Log deleted]'))

    def upgradeLog(self, log, newLogClass):
        self.processLogClass(newLogClass)
        prefix       = getPrefix(log)
        log.logClass = newLogClass
        newName      = newLogClass.name
        t(prefix)
        print(t.over(f'{prefix}[Upgrading to <{newName}>]'))
        return log

    def print(self, log, etype, data):
        if log.logClass.enList[etype.value]:
            prefix = getPrefix(log)
            ename  = etype.name
            data   = f'\t {repr(data)}' if data is not None else ''
            print(t(prefix + ename + data))


class Log:

    def __init__(self, myLogger, myID, logClass):
        self.myLogger = myLogger
        self.myID     = myID
        self.logClass = logClass
        self.entries  = []
        self.myLogger.logCreated(self)

    def __del__(self):
        if hasattr(self, 'myLogger'):
            self.myLogger.logDeleted(self)

    def __call__(self, etype, *data):
        # if   len(data) == 0: data = None
        # elif len(data) == 1: data = data[0]
        # self.entries.append((etype.value, repr(data)))
        self.myLogger.print(self, etype, data)

    def upgrade(self, newLogClass):
        return self.myLogger.upgradeLog(self, newLogClass)



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

