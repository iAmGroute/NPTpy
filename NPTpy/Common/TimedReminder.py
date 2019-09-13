
from .Reminder import Reminder
from .Timer    import Timer

class TimedReminder(Reminder):

    def __init__(self, *args, **kwargs):
        Reminder.__init__(self)
        self.timer = Timer(*args, **kwargs)

    def run(self):
        if self.timer.run():
            Reminder.run(self)

