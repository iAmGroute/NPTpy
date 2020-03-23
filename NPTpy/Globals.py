
from Common.Log           import Logger
from Common.TimedReminder import TimedReminder
from Common.Selectables   import Selectables

kaReminderRX    = TimedReminder(interval=30.0)
kaReminderTX    = TimedReminder(interval=10.0)
timeoutReminder = TimedReminder(interval= 4.0)

def runReminders():
    kaReminderRX.run()
    kaReminderTX.run()
    timeoutReminder.run()

readables = Selectables(timeoutReminder)
writables = Selectables(timeoutReminder)


logPrintLF = True
def logPrint(*args, **kwargs):
    global logPrintLF
    if 'end' in kwargs:
        if logPrintLF:
            logPrintLF = False
            print(flush=True)
    else:
        if not logPrintLF:
            logPrintLF = True
            print()
            print()
    print(*args, **kwargs)


logger = Logger(logPrint)
