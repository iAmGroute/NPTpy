
from NextLoop             import loop
from Common.TimedReminder import TimedReminder
from Common.Selectables   import Selectables

kaReminderRX    = TimedReminder(interval=30.0)
kaReminderTX    = TimedReminder(interval=10.0)
timeoutReminder = TimedReminder(interval= 4.0)

def runReminders():
    kaReminderRX.run()
    kaReminderTX.run()
    timeoutReminder.run()

readables = Selectables(loop, timeoutReminder)
writables = Selectables(loop, timeoutReminder)
