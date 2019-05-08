python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Servers.Relay import Relay

r = Relay(4021)

r.taskManage()

r.task()

r.task()

print(r.connSockets)
print(r.tokenMap)

while True:
    time.sleep(1)
    try:
        r.process(r.connSockets[0])
    except BlockingIOError:
        pass
    time.sleep(1)
    try:
        r.process(r.connSockets[1])
    except BlockingIOError:
        pass

