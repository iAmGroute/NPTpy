from enum import Enum

from Common.Log           import Logger
from Common.Reminder      import Reminder
from Common.TimedReminder import TimedReminder
from Common.Selectables   import Selectables

kaReminderRX  = TimedReminder(interval=30.0)
kaReminderTX  = TimedReminder(interval=10.0)

_reminders = Reminder()
reminders  = _reminders.new(onRun={ kaReminderRX.run, kaReminderTX.run })

readables = Selectables()
writables = Selectables()

logger = Logger()
