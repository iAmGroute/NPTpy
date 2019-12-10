import time

class Timer:

    def __init__(self, interval):
        self.interval  = interval
        self.time      = time.time()

    def run(self, reset=True):
        result = time.time() > self.time + self.interval
        if result and reset:
            self.time = time.time()
        return result

