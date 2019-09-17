from Common.Reminder      import Reminder
from Common.TimedReminder import TimedReminder

resetReminder = TimedReminder(interval=5.0)
kaReminderRX  = TimedReminder(interval=30.0)
kaReminderTX  = TimedReminder(interval=10.0)

_reminders = Reminder()
reminders  = _reminders.getDelegate(onRun={ resetReminder.run, kaReminderRX.run, kaReminderTX.run })
