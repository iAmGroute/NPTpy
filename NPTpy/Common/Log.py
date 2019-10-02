
import time

from .SmartTabs import t


class Logger:

    def __init__(self):
        self.logCount = 0

    def new(self, logType=None):
        logID = self.logCount
        self.logCount += 1
        return Log(self, logID, logType)

    def print(self, log, entryType, data):
        tstamp    = time.time()
        logID     = log.myID.to_bytes(4, 'big').hex().upper()
        logName   = log.logType.name
        entryName = entryType.name
        entryData = data
        print(t('{0:.1f}\t [{1}] {2}:\t {3} {4}'.format(tstamp, logID, logName, entryName, entryData)))


class Log:

    def __init__(self, myLogger, myID, logType=None):
        self.myLogger = myLogger
        self.myID     = myID
        self.logType  = logType
        self.entries  = []

    def __call__(self, entryType, data):
        # self.entries.append((entryType, data))
        self.myLogger.print(self, entryType, data)


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

