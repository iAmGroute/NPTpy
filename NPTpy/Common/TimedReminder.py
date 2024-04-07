
from .Reminder import T_link, Reminder
from .Timer    import Timer

class TimedReminder(Reminder[T_link]):

    def __init__(self, interval: float):
        super().__init__()
        self.timer = Timer(interval)

    def run(self):
        if self.timer.run():
            super().run()
