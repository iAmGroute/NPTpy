
import time

from enum import Enum

from .SmartTabs import t

class BasicEtypes(Enum):
    LogInited  = 0
    LogDeleted = 1

class Logger:

    def __init__(self):
        self.logCount = 0
        self.logTypes = []

    def getLogName(self, log):
        return self.logTypes[log.typeID].name

    def getLogTypeID(self, logClass):
        if not logClass.typeID:
            logClass.typeID = len(self.logTypes)
            self.logTypes.append(logClass)
        return logClass.typeID

    def new(self, logClass):
        logID = self.logCount
        self.logCount += 1
        typeID = self.getLogTypeID(logClass)
        return Log(self, logID, typeID)

    def upgradeLog(self, log, newLogClass):
        tstamp = time.time()
        print(t.over('{0:.1f}\t Changing log [{1}] from <{2}> to <{3}>'.format(
            tstamp, log.myID, self.getLogName(log), newLogClass.name
        )))
        log.typeID = self.getLogTypeID(newLogClass)

    def print(self, log, entryType, data):
        tstamp    = time.time()
        logID     = log.myID.to_bytes(4, 'big').hex().upper()
        logName   = self.getLogName(log)
        entryName = entryType.name
        entryData = data
        print(t('{0:.1f}\t [{1}] {2}:\t {3}\t {4}'.format(tstamp, logID, logName, entryName, entryData)))


class Log:

    def __init__(self, myLogger, myID, typeID):
        self.myLogger = myLogger
        self.myID     = myID
        self.typeID   = typeID
        self.entries  = []
        self.__call__(BasicEtypes.LogInited, ())

    def __del__(self):
        if hasattr(self, '__call__'):
            self.__call__(BasicEtypes.LogDeleted, ())

    def __call__(self, entryType, *data):
        # self.entries.append((entryType, data))
        self.myLogger.print(self, entryType, data)

    def upgrade(self, newLogClass):
        self.myLogger.upgradeLog(self, newLogClass)



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

#     def log(self, entryType, data):



# class LogContext:

#     def __init__(self, path):
#         self.path        = path
#         self.nodeCounter = 0

#     def __call__(self):
#         path = self.path + [self.nodeCounter]
#         self.nodeCounter += 1
#         return Log(path)

