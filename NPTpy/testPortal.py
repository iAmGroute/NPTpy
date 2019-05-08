python

import time
import logging
logging.basicConfig(format='%(created).3f [%(name)s|%(levelname)s] %(message)s', level=logging.INFO)

from Portal import Portal

p = Portal(b'ABCE')

while True:
    p.connectKA()
    while p.connected:
        p.task()
    time.sleep(1)

