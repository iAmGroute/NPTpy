
import time

class Timer:

    def __init__(self, interval: float):
        self.interval  = interval
        self.time      = time.time()

    def run(self, reset: bool = True):
        ready = time.time() > self.time + self.interval
        if ready and reset:
            self.time = time.time()
        return ready
